// Testbench for the Virtual JTAG register window. It drives the vJTAG signals the way
// the primitive presents them (ir_in, capture, shift, update); it is not a JTAG TAP model.
`timescale 1ns/1ps
module tb_vjtag;
    reg tck = 0, clk = 0;
    always #50 tck = ~tck;          // 10 MHz
    always #6.7 clk = ~clk;         // ~75 MHz, unrelated phase
    reg tdi = 0; reg [3:0] ir = 0; reg cdr = 0, sdr = 0, udr = 0;
    wire tdo;
    wire b_req, b_we, b_ack; wire [14:0] b_addr; wire [31:0] b_wdata, b_rdata;
    wire u_req, u_we, u_ack; wire [13:0] u_addr; wire [31:0] u_wdata;
    reg  [31:0] u_rdata = 0;
    reg  u_ack_en = 1;               // set 0 to make the user bus hang (timeout test)
    reg  u_ack_r = 0;
    assign u_ack = u_ack_en & u_ack_r;
    reg  tx_valid = 0; reg [7:0] tx_data = 0; wire tx_full;
    wire rx_valid; wire [7:0] rx_data; reg rx_ready = 0;

    pk_vjtag_regwin #(.TIMEOUT(1500)) dut (.tck(tck), .tdi(tdi), .tdo(tdo), .ir_in(ir),
        .v_cdr(cdr), .v_sdr(sdr), .v_udr(udr), .clk(clk), .bus_req(b_req), .bus_we(b_we),
        .bus_addr(b_addr), .bus_wdata(b_wdata), .bus_ack(b_ack), .bus_rdata(b_rdata));
    pk_debug_decode dec (.clk(clk), .b_req(b_req), .b_we(b_we), .b_addr(b_addr), .b_wdata(b_wdata),
        .b_ack(b_ack), .b_rdata(b_rdata), .u_req(u_req), .u_we(u_we), .u_addr(u_addr),
        .u_wdata(u_wdata), .u_ack(u_ack), .u_rdata(u_rdata), .tx_valid(tx_valid), .tx_data(tx_data),
        .tx_full(tx_full), .rx_valid(rx_valid), .rx_data(rx_data), .rx_ready(rx_ready));
    always @(posedge clk) begin u_ack_r <= u_req & ~u_ack_r; u_rdata <= {18'd0, u_addr}; end  // returns its address

    integer fails = 0, checks = 0;
    task check(input [255:0] name, input [47:0] got, input [47:0] exp);
        begin checks = checks + 1;
            if (got !== exp) begin fails = fails + 1; $display("FAIL %0s: got %h expected %h", name, got, exp); end
        end
    endtask

    // one DR transaction: capture, n shifts (LSB first), update. Returns shifted-out bits.
    reg [47:0] out;
    task dr(input [3:0] irv, input integer n, input [47:0] din);
        integer i;
        begin
            ir = irv; out = 0;
            @(posedge tck); #1 cdr = 1; @(posedge tck); #1 cdr = 0;
            for (i = 0; i < n; i = i + 1) begin
                tdi = din[i]; sdr = 1;
                #20 out[i] = tdo;       // sampled just before the shifting edge
                @(posedge tck); #1 sdr = 0;
            end
            udr = 1; @(posedge tck); #1 udr = 0; sdr = 0;
        end
    endtask
    task wait_idle; integer k; begin
        k = 0; out = 48'd0; out[33] = 1;
        while (out[33] && k < 50) begin dr(4'd2, 35, 0); k = k + 1; end
    end endtask
    task wr(input [14:0] a, input [31:0] d); begin dr(4'd1, 48, {1'b1, a, d}); wait_idle; end endtask
    task rd(input [14:0] a); begin dr(4'd1, 48, {1'b0, a, 32'd0}); wait_idle; end endtask

    initial begin
        #1000;
        dr(4'd3, 32, 0);                    check("id", out[31:0], 32'h504B_0101);
        rd(15'd0);                          check("demo id", out[31:0], 32'hD0C0_FFEE);
        wr(15'd1, 32'hCAFE_1234);           check("write ok err", out[32], 0);
        rd(15'd1);                          check("scratch", out[31:0], 32'hCAFE_1234);
        rd(15'd3);                          check("write count", out[31:0], 32'd1);
        rd(15'd2); begin : cnt reg [31:0] c1; c1 = out[31:0]; rd(15'd2);
            checks = checks + 1; if (!(out[31:0] > c1)) begin fails = fails + 1; $display("FAIL counter did not advance"); end end
        rd(15'h4123);                       check("user window", out[31:0], 32'h0000_0123);
        wr(15'h4040, 32'h1);                check("user write ok", out[32], 0);
        rd(15'h2000);                       check("unmapped", out[31:0], 32'hBAD0_ADD0);
        // timeout: user bus stops acknowledging
        u_ack_en = 0; rd(15'h4001);         check("timeout err", out[32], 1);
                                            check("timeout data", out[31:0], 32'hDEAD_BEEF);
        u_ack_en = 1; rd(15'd1);            check("recovers", out[31:0], 32'hCAFE_1234); check("recovers err", out[32], 0);
        // overrun: second REQ while busy is refused (stop acks, issue two requests)
        u_ack_en = 0; dr(4'd1, 48, {1'b0, 15'h4001, 32'd0}); dr(4'd1, 48, {1'b0, 15'd1, 32'd0});
        dr(4'd2, 35, 0);                    check("overrun flag", out[34], 1);
        u_ack_en = 1; wait_idle;
        // stream: core -> host
        @(posedge clk); tx_valid <= 1; tx_data <= 8'h48; @(posedge clk); tx_data <= 8'h69; @(posedge clk); tx_valid <= 0;
        rd(15'h1000);                       check("tx count", out[7:0], 8'd2);
        rd(15'h1001);                       check("tx byte 1", out[8:0], 9'h048);
        rd(15'h1001);                       check("tx byte 2", out[8:0], 9'h069);
        rd(15'h1001);                       check("tx empty", out[8:0], 9'h100);
        // stream: host -> core
        wr(15'h1002, 32'h5A);
        repeat (4) @(posedge clk);
        check("rx valid", rx_valid, 1); check("rx data", rx_data, 8'h5A);
        rx_ready = 1; @(posedge clk); #1 rx_ready = 0; repeat (2) @(posedge clk);
        check("rx drained", rx_valid, 0);
        $display("%0d checks, %0d failures", checks, fails);
        if (fails == 0) $display("PASS"); else $display("FAILED");
        $finish;
    end
    initial begin #20000000; $display("TIMEOUT"); $finish; end
endmodule
