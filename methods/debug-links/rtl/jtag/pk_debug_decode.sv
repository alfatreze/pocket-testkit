// Address decode shared by every link (Virtual JTAG, JTAG master, a UART): demo regs,
// byte stream, and a pass-through window for the user's own registers.
module pk_debug_decode (
    input  wire        clk,
    input  wire        b_req, b_we,
    input  wire [14:0] b_addr,
    input  wire [31:0] b_wdata,
    output wire        b_ack,
    output wire [31:0] b_rdata,
    output wire        u_req, u_we,
    output wire [13:0] u_addr,
    output wire [31:0] u_wdata,
    input  wire        u_ack,
    input  wire [31:0] u_rdata,
    input  wire        tx_valid,
    input  wire [7:0]  tx_data,
    output wire        tx_full,
    output wire        rx_valid,
    output wire [7:0]  rx_data,
    input  wire        rx_ready
);
    wire sel_demo = (b_addr[14:12] == 3'd0);
    wire sel_str  = (b_addr[14:12] == 3'd1);
    wire sel_user = b_addr[14];
    wire d_ack, s_ack;
    wire [31:0] d_rdata, s_rdata;
    pk_demo_regs u_demo (.clk(clk), .req(b_req & sel_demo), .we(b_we), .addr(b_addr[1:0]),
        .wdata(b_wdata), .ack(d_ack), .rdata(d_rdata));
    pk_reg_stream u_str (.clk(clk), .req(b_req & sel_str), .we(b_we), .addr(b_addr[1:0]),
        .wdata(b_wdata), .ack(s_ack), .rdata(s_rdata), .tx_valid(tx_valid), .tx_data(tx_data),
        .tx_full(tx_full), .rx_valid(rx_valid), .rx_data(rx_data), .rx_ready(rx_ready));
    assign u_req   = b_req & sel_user;
    assign u_we    = b_we;
    assign u_addr  = b_addr[13:0];
    assign u_wdata = b_wdata;
    assign b_ack   = sel_user ? u_ack : sel_str ? s_ack : sel_demo ? d_ack : b_req; // unmapped acks at once
    assign b_rdata = sel_user ? u_rdata : sel_str ? s_rdata : sel_demo ? d_rdata : 32'hBAD0_ADD0;
endmodule
