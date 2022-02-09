// Verifying a Counter
// Figure 2: A SystemVerilog counter

`timescale 1ns/1ns
module counter(input bit clk,
               input bit reset_n,
               output byte unsigned count);

    always @(posedge clk)
        count <= reset_n ? count + 1 : 'b0;

endmodule
