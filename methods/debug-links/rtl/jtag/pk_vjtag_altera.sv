// Quartus wrapper: the sld_virtual_jtag primitive plus pk_vjtag_regwin.
// NOT fitted or tested on hardware by this kit (see methods/debug-links/CHOOSING.md).
// Port and parameter names follow Intel's Virtual JTAG IP user guide; check them against
// your Quartus version's generated instance if the compile complains.
// SDC: declare the JTAG clock (altera_reserved_tck, a hidden port) and clk as asynchronous
// clock groups, for example set_clock_groups -asynchronous -group {altera_reserved_tck}
// -group {<your clk>}, or the tck <-> clk paths are timed as if related. The crossings are
// safe by protocol (toggle plus payload stable while busy), not by the analyser.
module pk_vjtag_altera #(
    parameter [31:0] ID = 32'h504B_0101,
    parameter        TIMEOUT = 1024,
    parameter        INSTANCE = 0
) (
    input  wire        clk,
    output wire        bus_req,
    output wire        bus_we,
    output wire [14:0] bus_addr,
    output wire [31:0] bus_wdata,
    input  wire        bus_ack,
    input  wire [31:0] bus_rdata
);
    wire tck, tdi, tdo, cdr, sdr, udr;
    wire [3:0] ir_in;
    sld_virtual_jtag #(
        .sld_auto_instance_index ("NO"),
        .sld_instance_index      (INSTANCE),
        .sld_ir_width            (4)
    ) u_vjtag (
        .tck(tck), .tdi(tdi), .tdo(tdo), .ir_in(ir_in), .ir_out(4'd0),
        .virtual_state_cdr(cdr), .virtual_state_sdr(sdr), .virtual_state_udr(udr),
        .virtual_state_e1dr(), .virtual_state_pdr(), .virtual_state_e2dr(),
        .virtual_state_cir(), .virtual_state_uir()
    );
    pk_vjtag_regwin #(.ID(ID), .TIMEOUT(TIMEOUT)) u_win (
        .tck(tck), .tdi(tdi), .tdo(tdo), .ir_in(ir_in),
        .v_cdr(cdr), .v_sdr(sdr), .v_udr(udr),
        .clk(clk), .bus_req(bus_req), .bus_we(bus_we), .bus_addr(bus_addr),
        .bus_wdata(bus_wdata), .bus_ack(bus_ack), .bus_rdata(bus_rdata)
    );
endmodule
