import logging
import time

from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import (
    CONFIG_DISPATCHER,
    MAIN_DISPATCHER,
    DEAD_DISPATCHER,
    set_ev_cls
)
from os_ken.ofproto import ofproto_v1_3
from os_ken.lib import hub
from os_ken.lib.packet import packet, ethernet, ether_types


class FileSharingController(app_manager.OSKenApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(FileSharingController, self).__init__(*args, **kwargs)

        self.mac_to_port = {}
        self.datapaths = {}
        self.previous_stats = {}

        self.logger.info("SDN File Sharing Controller initialized")

        hub.spawn(self._monitor)

    # --------------------------------------------------
    # ADD FLOW TO SWITCH
    # --------------------------------------------------

    def add_flow(self, datapath, priority, match, actions):

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        if actions:
            instructions = [
                parser.OFPInstructionActions(
                    ofproto.OFPIT_APPLY_ACTIONS,
                    actions
                )
            ]
        else:
            # Empty instructions mean DROP
            instructions = []

        flow_mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=instructions
        )

        datapath.send_msg(flow_mod)

    # --------------------------------------------------
    # SWITCH CONNECTION
    # --------------------------------------------------

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_connected(self, ev):

        datapath = ev.msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        self.logger.info(
            "SWITCH CONNECTED: DPID=%016x",
            datapath.id
        )

        # TABLE-MISS FLOW
        match = parser.OFPMatch()

        actions = [
            parser.OFPActionOutput(
                ofproto.OFPP_CONTROLLER,
                ofproto.OFPCML_NO_BUFFER
            )
        ]

        self.add_flow(datapath, 0, match, actions)

        self.logger.info("TABLE-MISS FLOW INSTALLED")

        # SDN ACCESS CONTROL POLICY
        # Block TCP from h1 to h2 on destination port 5002

        block_match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_src="10.0.0.1",
            ipv4_dst="10.0.0.2",
            ip_proto=6,
            tcp_dst=5002
        )

        self.add_flow(
            datapath,
            100,
            block_match,
            []
        )

        self.logger.info(
            "ACCESS POLICY INSTALLED: BLOCK TCP "
            "10.0.0.1 -> 10.0.0.2:5002"
        )

    # --------------------------------------------------
    # TRACK SWITCH CONNECTIONS
    # --------------------------------------------------

    @set_ev_cls(
        ofp_event.EventOFPStateChange,
        [MAIN_DISPATCHER, DEAD_DISPATCHER]
    )
    def switch_state_change(self, ev):

        datapath = ev.datapath

        if ev.state == MAIN_DISPATCHER:

            self.datapaths[datapath.id] = datapath

            self.logger.info(
                "DATAPATH REGISTERED: %016x",
                datapath.id
            )

        elif ev.state == DEAD_DISPATCHER:

            self.datapaths.pop(datapath.id, None)

            self.logger.info(
                "DATAPATH REMOVED: %016x",
                datapath.id
            )

    # --------------------------------------------------
    # PACKET-IN HANDLER: LEARNING SWITCH
    # --------------------------------------------------

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):

        msg = ev.msg
        datapath = msg.datapath

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        in_port = msg.match["in_port"]

        pkt = packet.Packet(msg.data)

        eth = pkt.get_protocol(ethernet.ethernet)

        if eth is None:
            return

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        dst = eth.dst
        src = eth.src

        dpid = datapath.id

        self.mac_to_port.setdefault(dpid, {})

        # Learn source MAC address
        self.mac_to_port[dpid][src] = in_port

        # Find destination port
        out_port = self.mac_to_port[dpid].get(
            dst,
            ofproto.OFPP_FLOOD
        )

        actions = [
            parser.OFPActionOutput(out_port)
        ]

        # Install forwarding flow for known destination
        if out_port != ofproto.OFPP_FLOOD:

            match = parser.OFPMatch(
                in_port=in_port,
                eth_src=src,
                eth_dst=dst
            )

            self.add_flow(
                datapath,
                1,
                match,
                actions
            )

        # Send packet out
        data = None

        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data
        )

        datapath.send_msg(out)

    # --------------------------------------------------
    # BANDWIDTH MONITORING
    # --------------------------------------------------

    def _monitor(self):

        while True:

            for datapath in list(self.datapaths.values()):

                parser = datapath.ofproto_parser

                request = parser.OFPFlowStatsRequest(datapath)

                datapath.send_msg(request)

            hub.sleep(5)

    # --------------------------------------------------
    # FLOW STATISTICS REPLY
    # --------------------------------------------------

    @set_ev_cls(
        ofp_event.EventOFPFlowStatsReply,
        MAIN_DISPATCHER
    )
    def flow_stats_handler(self, ev):

        datapath = ev.msg.datapath
        dpid = datapath.id

        current_time = time.time()

        for stat in ev.msg.body:

            if stat.priority <= 0:
                continue

            match = stat.match

            in_port = match.get("in_port", 0)
            eth_src = match.get("eth_src", "")
            eth_dst = match.get("eth_dst", "")

            # Ignore flows without learned MAC addresses
            if not eth_src or not eth_dst:
                continue

            byte_count = stat.byte_count
            packet_count = stat.packet_count

            key = (
                dpid,
                in_port,
                eth_src,
                eth_dst
            )

            previous = self.previous_stats.get(key)

            if previous is not None:

                old_bytes, old_packets, old_time = previous

                elapsed = current_time - old_time

                if elapsed > 0:

                    byte_difference = max(
                        0,
                        byte_count - old_bytes
                    )

                    packet_difference = max(
                        0,
                        packet_count - old_packets
                    )

                    # Convert bytes per second to Kbps
                    bandwidth = (
                        byte_difference * 8
                    ) / (elapsed * 1000)

                    packets_per_second = (
                        packet_difference / elapsed
                    )

                    self.logger.info(
                        "BANDWIDTH: DPID=%016x "
                        "SRC=%s DST=%s "
                        "RATE=%.2f Kbps "
                        "PACKETS/SEC=%.2f",
                        dpid,
                        eth_src,
                        eth_dst,
                        bandwidth,
                        packets_per_second
                    )

            self.previous_stats[key] = (
                byte_count,
                packet_count,
                current_time
            )
