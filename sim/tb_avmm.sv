`timescale 1ns/1ps
module tb_avmm;
    reg clk = 0; always #5 clk = ~clk;
    reg [31:0] addr = 0, wd = 0; reg rd = 0, wr = 0;
    wire wait_, rdv; wire [31:0] rdat;
    wire req, we, ack; wire [14:0] baddr; wire [31:0] bwd, brd;
    pk_avmm_master_to_bus dut (.clk(clk), .m_address(addr), .m_read(rd), .m_write(wr), .m_writedata(wd),
        .m_waitrequest(wait_), .m_readdatavalid(rdv), .m_readdata(rdat),
        .bus_req(req), .bus_we(we), .bus_addr(baddr), .bus_wdata(bwd), .bus_ack(ack), .bus_rdata(brd));
    pk_demo_regs regs (.clk(clk), .req(req & (baddr[14:2]==0)), .we(we), .addr(baddr[1:0]), .wdata(bwd), .ack(ack), .rdata(brd));
    integer fails = 0;
    task access(input w, input [31:0] a, input [31:0] d);
        begin
            @(posedge clk); #1 addr = a; wd = d; rd = !w; wr = w;
            @(posedge clk); while (wait_) @(posedge clk);
            #1 rd = 0; wr = 0;
        end
    endtask
    reg [31:0] got;
    initial begin
        #50;
        access(1, 32'h4, 32'hA5A5_0001);           // word 1 (byte address 4)
        access(0, 32'h4, 0);
        if (!rdv || rdat !== 32'hA5A5_0001) begin fails = fails + 1; $display("FAIL read back %h valid %b", rdat, rdv); end
        access(0, 32'h0, 0);
        if (!rdv || rdat !== 32'hD0C0_FFEE) begin fails = fails + 1; $display("FAIL id %h", rdat); end
        if (fails == 0) $display("PASS"); else $display("FAILED");
        $finish;
    end
endmodule
