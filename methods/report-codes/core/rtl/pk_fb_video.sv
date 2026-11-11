// Framebuffer viewer for an Analogue Pocket core: a data slot (the bridge) writes a raw RGB565 picture into block RAM, and a
// fixed video timing generator scans it out. Written for pocket-testkit; the Pocket template's own files are not included.
//
// Picture file: W x H pixels, 16 bits each, row by row, BIG-ENDIAN (the high byte first), so the first file byte lands in
// bridge_wr_data[31:24] when bridge_endian_little = 0 (the template default). If the colours look wrong on a real Pocket, the
// two interact-menu switches fix it without a rebuild: "swap bytes" (bridge address 0x20000000, for low-byte-first words) and
// "swap pixels" (0x20000004, the two pixels of a word the other way round). Not run on hardware by this kit.
//
// Video: ~12.288 MHz pixel clock, H_TOTAL x V_TOTAL = 400 x 512 clocks per frame = 60.000 Hz, active W x H at (H_BP, V_BP).
// RGB565 is expanded to RGB888 by bit replication, which is what python/tpg.py to_rgb assumes of a screenshot.
module pk_fb_video #(
    parameter H_ACTIVE = 320, V_ACTIVE = 240,
    parameter H_TOTAL = 400, V_TOTAL = 512, H_BP = 10, V_BP = 10
) (
    // bridge side (clk_74a)
    input  wire        clk_bridge,
    input  wire        bridge_wr,
    input  wire [31:0] bridge_addr,
    input  wire [31:0] bridge_wr_data,
    // video side
    input  wire        clk_vid,
    input  wire        reset_n,
    output reg  [23:0] rgb = 24'd0,
    output reg         de = 1'b0,
    output reg         skip = 1'b0,
    output reg         vs = 1'b0,
    output reg         hs = 1'b0
);
    localparam PIXELS = H_ACTIVE * V_ACTIVE;
    localparam WORDS  = PIXELS / 2;                       // 32-bit words; H_ACTIVE * V_ACTIVE must be even
    localparam AW     = $clog2(WORDS);

    // ---- framebuffer: simple dual-port RAM, written on clk_bridge, read on clk_vid ------------------------------
    (* ramstyle = "M10K, no_rw_check" *) reg [31:0] mem [0:WORDS-1];
    reg        we_r = 1'b0;
    reg [AW-1:0] wa_r = 0;
    reg [31:0] wd_r = 32'd0;
    wire sel = bridge_wr && (bridge_addr[31:24] == 8'h10) && ((bridge_addr[27:2]) < WORDS);
    reg swap_bytes = 1'b0, swap_pixels = 1'b0;           // interact-menu switches (write-only registers, bridge domain)
    always @(posedge clk_bridge) begin
        we_r <= sel; wa_r <= bridge_addr[2 +: AW]; wd_r <= bridge_wr_data;
        if (we_r) mem[wa_r] <= wd_r;
        if (bridge_wr && bridge_addr[31:24] == 8'h20) begin
            if (bridge_addr[3:2] == 2'd0) swap_bytes  <= bridge_wr_data[0];
            if (bridge_addr[3:2] == 2'd1) swap_pixels <= bridge_wr_data[0];
        end
    end

    // ---- timing counters (video clock), after the Pocket template's structure ---------------------------------
    reg [9:0]  x = 10'd0, y = 10'd0;
    reg [20:0] pix = 21'd0;                               // index of the current active pixel
    wire act = (x >= H_BP) && (x < H_BP + H_ACTIVE) && (y >= V_BP) && (y < V_BP + V_ACTIVE);
    wire [AW-1:0] raddr = pix[AW:1];
    reg [31:0] q = 32'd0;
    always @(posedge clk_vid) q <= mem[raddr];            // read port: no reset, so it maps to the RAM's output register
    reg        half = 1'b0, act_d = 1'b0, vs_d = 1'b0, hs_d = 1'b0;
    reg        sb_s = 1'b0, sp_s = 1'b0, sb_m = 1'b0, sp_m = 1'b0;   // two-flop sync of the near-static switches

    always @(posedge clk_vid or negedge reset_n) begin
        if (!reset_n) begin
            x <= 0; y <= 0; pix <= 0;
            rgb <= 0; de <= 0; vs <= 0; hs <= 0; skip <= 0;
            act_d <= 0; vs_d <= 0; hs_d <= 0; half <= 0;
        end else begin
            sb_m <= swap_bytes; sb_s <= sb_m; sp_m <= swap_pixels; sp_s <= sp_m;
            // stage 0: counters and the read address
            x <= x + 1'b1;
            if (x == H_TOTAL - 1) begin x <= 0; y <= y + 1'b1; if (y == V_TOTAL - 1) y <= 0; end
            if (x == 0 && y == 0) pix <= 0; else if (act) pix <= pix + 1'b1;
            half <= pix[0]; act_d <= act;
            vs_d <= (x == 0 && y == 0);
            hs_d <= (x == 3);
            // stage 1: pick the pixel and expand it
            de <= act_d; vs <= vs_d; hs <= hs_d; skip <= 1'b0;
            if (act_d) rgb <= expand(select(q, half, sb_s, sp_s)); else rgb <= 24'd0;
        end
    end

    function [15:0] select(input [31:0] w, input h, input sb, input sp);
        reg [15:0] px;
        begin
            px = (h ^ sp) ? w[15:0] : w[31:16];           // pixel 2k is the high half unless swapped
            select = sb ? {px[7:0], px[15:8]} : px;
        end
    endfunction
    function [23:0] expand(input [15:0] p);
        begin expand = {p[15:11], p[15:13], p[10:5], p[10:9], p[4:0], p[4:2]}; end
    endfunction
endmodule
