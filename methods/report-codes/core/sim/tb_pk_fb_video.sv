// Testbench: load a picture through bridge writes, capture one video frame as a PPM, check timing.
//   vvp tb.vvp +img=page.bin +out=frame.ppm [+sb=1] [+sp=1]
`timescale 1ns/1ps
module tb_pk_fb_video;
    localparam W = 320, H = 240, BYTES = W * H * 2;
    reg clk_bridge = 0, clk_vid = 0, reset_n = 0;
    always #6.734 clk_bridge = ~clk_bridge;       // 74.25 MHz
    always #40.69 clk_vid = ~clk_vid;             // 12.288 MHz, unrelated phase
    reg bridge_wr = 0; reg [31:0] bridge_addr = 0, bridge_wr_data = 0;
    wire [23:0] rgb; wire de, skip, vs, hs;
    pk_fb_video dut (.clk_bridge(clk_bridge), .bridge_wr(bridge_wr), .bridge_addr(bridge_addr), .bridge_wr_data(bridge_wr_data),
        .clk_vid(clk_vid), .reset_n(reset_n), .rgb(rgb), .de(de), .skip(skip), .vs(vs), .hs(hs));
    reg [7:0] img [0:BYTES-1];
    integer i, fd, n, x, y, frames, lines, de_n, vs_n, last_vs_t, vs_period, hs_n, hs_off, hs_first;
    reg [1023:0] imgf, outf;
    reg [7:0] frame [0:W*H*3-1];
    integer idx;
    initial begin
        if (!$value$plusargs("img=%s", imgf)) begin $display("FAIL no +img"); $finish; end
        if (!$value$plusargs("out=%s", outf)) begin $display("FAIL no +out"); $finish; end
        for (i = 0; i < BYTES; i = i + 1) img[i] = 8'h00;
        fd = $fopen(imgf, "rb"); n = $fread(img, fd); $fclose(fd);
        if (n != BYTES) begin $display("FAIL image has %0d bytes, expected %0d", n, BYTES); $finish; end
        #200 reset_n = 1;
        // interact switches are plain bridge writes to 0x20000000 (swap bytes) and 0x20000004 (swap pixels)
        if ($test$plusargs("sb")) begin @(posedge clk_bridge); #1 bridge_wr = 1; bridge_addr = 32'h20000000; bridge_wr_data = 1; @(posedge clk_bridge); #1 bridge_wr = 0; end
        if ($test$plusargs("sp")) begin @(posedge clk_bridge); #1 bridge_wr = 1; bridge_addr = 32'h20000004; bridge_wr_data = 1; @(posedge clk_bridge); #1 bridge_wr = 0; end
        // the data loader: one 32-bit word every 8 bridge clocks, first file byte in bits [31:24]
        for (i = 0; i < BYTES; i = i + 4) begin
            @(posedge clk_bridge); #1 bridge_wr = 1; bridge_addr = 32'h10000000 + i;
            bridge_wr_data = {img[i], img[i+1], img[i+2], img[i+3]};
            @(posedge clk_bridge); #1 bridge_wr = 0;
            repeat (6) @(posedge clk_bridge);
        end
        repeat (8) @(posedge clk_bridge);
        // capture the next whole frame: wait for vs, then collect active pixels until the following vs
        frames = 0; idx = 0; de_n = 0; vs_n = 0; hs_n = 0; hs_first = 0; hs_off = 0;
        @(posedge vs); last_vs_t = $time;
        while (vs_n < 1) begin
            @(posedge clk_vid); #1;
            if (de) begin
                if (idx < W*H*3) begin frame[idx] = rgb[23:16]; frame[idx+1] = rgb[15:8]; frame[idx+2] = rgb[7:0]; idx = idx + 3; end
                de_n = de_n + 1;
            end
            if (hs) begin hs_n = hs_n + 1; if (hs_first == 0) begin hs_first = 1; hs_off = $time - last_vs_t; end end
            if (vs) vs_n = vs_n + 1;
        end
        vs_period = $time - last_vs_t;
        fd = $fopen(outf, "wb");
        $fwrite(fd, "P6\n%0d %0d\n255\n", W, H);
        for (i = 0; i < W*H*3; i = i + 1) $fwrite(fd, "%c", frame[i]);
        $fclose(fd);
        $display("active pixels %0d (expected %0d)", de_n, W*H);
        $display("frame period %0d ns (expected about 16666667 ns for 60 Hz)", vs_period);
        $display("hs pulses per frame %0d (expected 512), first hs %0d ns after vs (expected 3 pixel clocks = about 244 ns)", hs_n, hs_off);
        if (de_n == W*H && vs_period > 16600000 && vs_period < 16730000 && hs_n == 512 && hs_off > 200 && hs_off < 290) $display("PASS"); else $display("FAILED");
        $finish;
    end
    initial begin #400000000 $display("TIMEOUT"); $finish; end
endmodule
