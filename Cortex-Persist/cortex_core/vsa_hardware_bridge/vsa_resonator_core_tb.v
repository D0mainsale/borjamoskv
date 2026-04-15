`timescale 1ns / 1ps

module vsa_resonator_core_tb;

    parameter BUS_WIDTH = 256;
    parameter DISTANCE_WIDTH = 9;

    reg clk;
    reg rst_n;
    reg [BUS_WIDTH-1:0] noisy_tensor;
    reg [BUS_WIDTH-1:0] query_tensor;
    reg [DISTANCE_WIDTH-1:0] threshold;
    reg resonate_enable;

    wire [DISTANCE_WIDTH-1:0] hamming_distance;
    wire match_found;
    wire valid;

    vsa_resonator_core #(
        .BUS_WIDTH(BUS_WIDTH),
        .DISTANCE_WIDTH(DISTANCE_WIDTH)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .noisy_tensor(noisy_tensor),
        .query_tensor(query_tensor),
        .threshold(threshold),
        .resonate_enable(resonate_enable),
        .hamming_distance(hamming_distance),
        .match_found(match_found),
        .valid(valid)
    );

    // 100MHz Target
    always #5 clk = ~clk;

    initial begin
        $dumpfile("resonator_core.vcd");
        $dumpvars(0, vsa_resonator_core_tb);

        clk = 0;
        rst_n = 0;
        resonate_enable = 0;
        // Accept up to 10% Noise (25 bit-flips max)
        threshold = 9'd25; 
        
        // Base Codebook Tensor
        query_tensor = { {128{2'b10}} }; 
        noisy_tensor = { {128{2'b10}} }; 

        #15 rst_n = 1;
        #10;
        
        // --- Test 1: Exact Convergence ---
        resonate_enable = 1;
        #10;
        resonate_enable = 0;
        $display("[ULTRATHINK] Test 1: Distance: %d, Match: %b", hamming_distance, match_found);
        
        #10;

        // --- Test 2: Unbinding Denoising ---
        // Injecting hardware noise: 16 absolute bit-flips
        noisy_tensor[255:240] = ~query_tensor[255:240]; 
        resonate_enable = 1;
        #10;
        resonate_enable = 0;
        $display("[ULTRATHINK] Test 2 (Noise): Expected Distance: 16. Actual Distance: %d, Match: %b", hamming_distance, match_found);
        
        if (hamming_distance === 9'd16 && match_found === 1'b1) begin
             $display("[MOSKV-1] VALIDATION PASS: Resonator Core successfully factors identity within 1 clock cycle (O(1)).");
        end else begin
             $display("[MOSKV-1] VALIDATION FAIL: Algorithmic Noise Detected.");
        end

        #20 $finish;
    end
endmodule
