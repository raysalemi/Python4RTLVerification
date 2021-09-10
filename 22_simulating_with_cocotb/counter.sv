`timescale 1ns/1ns
module counter(output bit clk,
               input bit reset_n,
               output byte unsigned count);

    initial begin
        clk = 0;
        count = 0;
    end

    always #5ns clk = ~clk;

    always @(posedge clk) 
        count <= reset_n ? count + 1 : 'b0;

endmodule
