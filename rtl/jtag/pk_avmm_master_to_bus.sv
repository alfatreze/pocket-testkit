// For the JTAG-to-Avalon master path: adapts the master's exported Avalon-MM master
// signals (from Platform Designer) to the same request/ack register bus used by the
// Virtual JTAG window. The register bus has ONE master port: if both links are built in,
// add an arbiter in front of it; simultaneous use corrupts accesses. clk must be the clock
// of the Avalon master bridge. Byte enables are ignored (every write is a full word).
// The master bridge expects waitrequest and readdatavalid; this gives both.
module pk_avmm_master_to_bus #(parameter ADDR_SHIFT = 2) (
    input  wire        clk,
    // exported Avalon-MM master (we are the slave side of it)
    input  wire [31:0] m_address,
    input  wire        m_read,
    input  wire        m_write,
    input  wire [31:0] m_writedata,
    output wire        m_waitrequest,
    output reg         m_readdatavalid = 1'b0,
    output reg  [31:0] m_readdata = 32'd0,
    // register bus
    output wire        bus_req,
    output wire        bus_we,
    output wire [14:0] bus_addr,
    output wire [31:0] bus_wdata,
    input  wire        bus_ack,
    input  wire [31:0] bus_rdata
);
    assign bus_req   = m_read | m_write;
    assign bus_we    = m_write;
    assign bus_addr  = m_address[ADDR_SHIFT +: 15];
    assign bus_wdata = m_writedata;
    assign m_waitrequest = bus_req & ~bus_ack;
    always @(posedge clk) begin
        m_readdatavalid <= m_read & bus_ack;
        m_readdata      <= bus_rdata;
    end
endmodule
