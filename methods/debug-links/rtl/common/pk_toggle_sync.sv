// Toggle synchroniser: a single-bit level toggled in the source domain becomes a
// one-clock pulse in the destination domain. Single bit only (see KB-009: never use
// this per bit on a bus). The attribute keeps Quartus from turning the chain into
// block RAM (KB-010).
module pk_toggle_sync (
    input  wire clk,      // destination clock
    input  wire t_in,     // toggles once per event, from another clock domain
    output wire pulse     // one clk cycle per toggle
);
    (* altera_attribute = "-name AUTO_SHIFT_REGISTER_RECOGNITION OFF" *)
    reg [2:0] s = 3'b000;
    always @(posedge clk) s <= {s[1:0], t_in};
    assign pulse = s[2] ^ s[1];
endmodule
