// One instance to add a Virtual JTAG register window to a core.
// Address map (word address, 15 bits):
//   0x0000-0x0003 demo/self-test regs     0x1000-0x1002 byte stream (see pk_reg_stream)
//   0x4000-0x7FFF your own registers, forwarded on the u_* port (word address in u_addr)
module pk_vjtag_debug #(parameter TIMEOUT = 1024) (
    input  wire        clk,
    // your registers
    output wire        u_req,
    output wire        u_we,
    output wire [13:0] u_addr,
    output wire [31:0] u_wdata,
    input  wire        u_ack,
    input  wire [31:0] u_rdata,
    // byte stream to and from the core
    input  wire        tx_valid,
    input  wire [7:0]  tx_data,
    output wire        tx_full,
    output wire        rx_valid,
    output wire [7:0]  rx_data,
    input  wire        rx_ready
);
    wire        b_req, b_we, b_ack;
    wire [14:0] b_addr;
    wire [31:0] b_wdata, b_rdata;
    pk_vjtag_altera #(.TIMEOUT(TIMEOUT)) u_link (
        .clk(clk), .bus_req(b_req), .bus_we(b_we), .bus_addr(b_addr),
        .bus_wdata(b_wdata), .bus_ack(b_ack), .bus_rdata(b_rdata));
    pk_debug_decode u_dec (
        .clk(clk), .b_req(b_req), .b_we(b_we), .b_addr(b_addr), .b_wdata(b_wdata),
        .b_ack(b_ack), .b_rdata(b_rdata),
        .u_req(u_req), .u_we(u_we), .u_addr(u_addr), .u_wdata(u_wdata),
        .u_ack(u_ack), .u_rdata(u_rdata),
        .tx_valid(tx_valid), .tx_data(tx_data), .tx_full(tx_full),
        .rx_valid(rx_valid), .rx_data(rx_data), .rx_ready(rx_ready));
endmodule
