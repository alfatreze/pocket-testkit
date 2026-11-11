// Byte stream over the register bus: a console or log out of the core (tx) and bytes
// into the core (rx). The JTAG UART idea without the Nios tools: the host polls.
// word 0 STATUS (read): [7:0] tx bytes waiting for the host, [15:8] rx free space
// word 1 TXDATA (read pops one byte): [8] = 1 when empty, [7:0] data
// word 2 RXDATA (write pushes one byte into the core)
module pk_reg_stream #(parameter DEPTH_LOG2 = 6) (
    input  wire       clk,
    // register bus slave
    input  wire       req,
    input  wire       we,
    input  wire [1:0] addr,
    input  wire [31:0] wdata,
    output reg        ack = 1'b0,
    output reg [31:0] rdata = 32'd0,
    // core side
    input  wire       tx_valid,      // core pushes a byte
    input  wire [7:0] tx_data,
    output wire       tx_full,
    output wire       rx_valid,      // a byte for the core, hold until rx_ready
    output wire [7:0] rx_data,
    input  wire       rx_ready
);
    localparam N = 1 << DEPTH_LOG2;
    reg [7:0] txm [0:N-1];
    reg [7:0] rxm [0:N-1];
    reg [DEPTH_LOG2:0] tx_w = 0, tx_r = 0, rx_w = 0, rx_r = 0;
    wire [DEPTH_LOG2:0] tx_n = tx_w - tx_r;
    wire [DEPTH_LOG2:0] rx_n = rx_w - rx_r;
    assign tx_full  = (tx_n == N);
    assign rx_valid = (rx_n != 0);
    assign rx_data  = rxm[rx_r[DEPTH_LOG2-1:0]];

    always @(posedge clk) begin
        ack <= 1'b0;
        if (tx_valid && !tx_full) begin
            txm[tx_w[DEPTH_LOG2-1:0]] <= tx_data;
            tx_w <= tx_w + 1'b1;
        end
        if (rx_valid && rx_ready) rx_r <= rx_r + 1'b1;
        if (req && !ack) begin
            ack <= 1'b1;
            case (addr)
                2'd0: rdata <= {16'd0, 8'(N - rx_n), 8'(tx_n)};
                2'd1: begin
                    if (tx_n != 0) begin
                        rdata <= {23'd0, 1'b0, txm[tx_r[DEPTH_LOG2-1:0]]};
                        if (!we) tx_r <= tx_r + 1'b1;
                    end else rdata <= 32'h0000_0100;
                end
                default: rdata <= 32'd0;
            endcase
            if (we && addr == 2'd2 && rx_n != N) begin
                rxm[rx_w[DEPTH_LOG2-1:0]] <= wdata[7:0];
                rx_w <= rx_w + 1'b1;
            end
        end
    end
endmodule
