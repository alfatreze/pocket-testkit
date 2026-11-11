// Self-test register bank: proves the link end to end before you wire real registers.
// word 0: ID (read) = 32'hD0C0_FFEE   word 1: scratch (read/write)
// word 2: free-running counter (read) word 3: write counter (read)
module pk_demo_regs (
    input  wire        clk,
    input  wire        req,
    input  wire        we,
    input  wire [1:0]  addr,
    input  wire [31:0] wdata,
    output reg         ack = 1'b0,
    output reg  [31:0] rdata = 32'd0
);
    reg [31:0] scratch = 32'd0, free = 32'd0, writes = 32'd0;
    always @(posedge clk) begin
        free <= free + 1'b1;
        ack  <= 1'b0;
        if (req && !ack) begin
            ack <= 1'b1;
            if (we) begin
                if (addr == 2'd1) scratch <= wdata;
                writes <= writes + 1'b1;
            end
            case (addr)
                2'd0: rdata <= 32'hD0C0_FFEE;
                2'd1: rdata <= scratch;
                2'd2: rdata <= free;
                2'd3: rdata <= writes;
            endcase
        end
    end
endmodule
