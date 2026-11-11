// Register window over Virtual JTAG: read and write 32-bit words on a simple
// request/ack register bus, from a PC, through the USB Blaster. No Platform Designer,
// no Avalon, no soft CPU needed. Pure RTL: the vendor primitive is in pk_vjtag_altera.sv,
// so this file can be simulated with any simulator.
//
// Virtual IR values (ir_in), 4 bits:
//   0 bypass   1 REQ (DR 48 bits, shift in {we, addr[14:0], wdata[31:0]}, issued on update)
//   2 RSP (DR 35 bits captured: [31:0] rdata, [32] err (bus timeout), [33] busy, [34] overrun)
//   3 ID  (DR 32 bits captured: ID parameter)
// All DRs shift LSB first.
//
// Clocking: tck is the JTAG clock (<= 24 MHz with a Blaster, often 6 to 10). clk is your
// register-bus clock; keep clk at least 2x tck (Intel's advice for the JTAG master, applied
// here as a safe rule). Crossing: one toggle each way plus payload registers that are
// stable whenever the toggle is seen, because a new request is refused while busy.
module pk_vjtag_regwin #(
    parameter [31:0] ID      = 32'h504B_0101,  // "PK" 01.01
    parameter        TIMEOUT = 1024            // clk cycles to wait for bus_ack
) (
    // Virtual JTAG side (tck domain)
    input  wire        tck,
    input  wire        tdi,
    output wire        tdo,
    input  wire [3:0]  ir_in,
    input  wire        v_cdr,
    input  wire        v_sdr,
    input  wire        v_udr,
    // Register bus (clk domain)
    input  wire        clk,
    output reg         bus_req = 1'b0,
    output reg         bus_we = 1'b0,
    output reg  [14:0] bus_addr = 15'd0,
    output reg  [31:0] bus_wdata = 32'd0,
    input  wire        bus_ack,
    input  wire [31:0] bus_rdata
);
    // ---- tck domain ---------------------------------------------------------------
    reg [47:0] sh = 48'd0;
    reg        byp = 1'b0;
    reg        req_t = 1'b0;                 // toggles when a request is issued
    reg [47:0] req_frame = 48'd0;            // stable while busy
    reg        overrun = 1'b0;
    reg [1:0]  ack_s = 2'b00;                // ack toggle, synchronised into tck
    wire       ack_t_tck;
    reg        ack_t = 1'b0;                 // owned by clk domain
    reg [31:0] rsp_data = 32'd0;             // owned by clk domain, stable while idle
    reg        rsp_err = 1'b0;

    always @(posedge tck) ack_s <= {ack_s[0], ack_t};
    assign ack_t_tck = ack_s[1];
    wire busy = (req_t != ack_t_tck);

    always @(posedge tck) begin
        byp <= tdi;
        if (v_cdr) begin
            case (ir_in)
                4'd2:    sh <= {13'd0, overrun, busy, rsp_err, rsp_data};
                4'd3:    sh <= {16'd0, ID};
                default: sh <= 48'd0;
            endcase
        end else if (v_sdr) begin
            sh <= {tdi, sh[47:1]};
        end
        if (v_udr && ir_in == 4'd1) begin
            if (busy) begin
                overrun <= 1'b1;
            end else begin
                req_frame <= sh;
                req_t     <= ~req_t;
                overrun   <= 1'b0;
            end
        end
    end
    assign tdo = (ir_in == 4'd0) ? byp : sh[0];

    // ---- clk domain ---------------------------------------------------------------
    wire req_pulse;
    pk_toggle_sync u_req (.clk(clk), .t_in(req_t), .pulse(req_pulse));

    reg [$clog2(TIMEOUT+1):0] wait_cnt = 0;
    always @(posedge clk) begin
        if (req_pulse && !bus_req) begin
            bus_req   <= 1'b1;
            bus_we    <= req_frame[47];
            bus_addr  <= req_frame[46:32];
            bus_wdata <= req_frame[31:0];
            wait_cnt  <= 0;
        end else if (bus_req) begin
            if (bus_ack) begin
                bus_req  <= 1'b0;
                rsp_data <= bus_rdata;
                rsp_err  <= 1'b0;
                ack_t    <= ~ack_t;
            end else if (wait_cnt == TIMEOUT) begin
                bus_req  <= 1'b0;
                rsp_data <= 32'hDEAD_BEEF;
                rsp_err  <= 1'b1;
                ack_t    <= ~ack_t;
            end else begin
                wait_cnt <= wait_cnt + 1'b1;
            end
        end
    end
endmodule
