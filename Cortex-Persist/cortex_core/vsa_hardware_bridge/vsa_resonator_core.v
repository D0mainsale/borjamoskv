`timescale 1ns / 1ps

/*
 * CORTEX Law Ω0 Enforcement.
 * ULTRATHINK Protocol: VSA Resonator Core
 * Synthesizes Popcount-based Hamming Distance evaluation for Vector Disentanglement.
 */
module vsa_resonator_core #(
    parameter BUS_WIDTH = 256,
    parameter DISTANCE_WIDTH = 9 // log2(256) is 8. Added 1 for max threshold 256.
)(
    input  wire                 clk,
    input  wire                 rst_n,
    input  wire [BUS_WIDTH-1:0] noisy_tensor,
    input  wire [BUS_WIDTH-1:0] query_tensor,
    input  wire [DISTANCE_WIDTH-1:0] threshold,
    input  wire                 resonate_enable,
    output reg  [DISTANCE_WIDTH-1:0] hamming_distance,
    output reg                  match_found,
    output reg                  valid
);

    // 1. Unbind Operator (XOR provides difference)
    wire [BUS_WIDTH-1:0] unbound_diff;
    assign unbound_diff = noisy_tensor ^ query_tensor;
    
    // 2. Unpipelined Combinational Popcount (Adder Tree)
    integer i;
    reg [DISTANCE_WIDTH-1:0] comb_count;
    
    always @* begin
        comb_count = 0;
        for (i = 0; i < BUS_WIDTH; i = i + 1) begin
            comb_count = comb_count + unbound_diff[i];
        end
    end

    // 3. Output Stage (O(1) latency from combinational setup)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            hamming_distance <= 0;
            match_found      <= 1'b0;
            valid            <= 1'b0;
        end else if (resonate_enable) begin
            hamming_distance <= comb_count;
            match_found      <= (comb_count <= threshold) ? 1'b1 : 1'b0;
            valid            <= 1'b1;
        end else begin
            valid            <= 1'b0;
        end
    end

endmodule
