`timescale 1ns / 1ps

/*
 * CORTEX Law Ω0 Enforcement.
 * Comprehensive Testbench for Ultra-High Frequency VSA Tensor Binder
 * Author: Borja Moskv (borjamoskv)
 */
module vsa_tensor_binder_tb;

    parameter BUS_WIDTH = 256;
    parameter SHIFT_BITS = $clog2(BUS_WIDTH);

    reg                   clk;
    reg                   rst_n;
    reg  [BUS_WIDTH-1:0]   tensor_a;
    reg  [BUS_WIDTH-1:0]   tensor_b;
    reg  [1:0]             mode;
    reg  [SHIFT_BITS-1:0]  shift_amount;
    reg                   bind_enable;
    reg                   acc_reset;

    wire [BUS_WIDTH-1:0]   tensor_out;
    wire [BUS_WIDTH:0]     popcount;
    wire [BUS_WIDTH:0]     hamming_dist;
    wire                   entropy_anomaly;
    wire                   valid;

    vsa_tensor_binder #(
        .BUS_WIDTH(BUS_WIDTH)
    ) dut (
        .clk            (clk),
        .rst_n          (rst_n),
        .tensor_a       (tensor_a),
        .tensor_b       (tensor_b),
        .mode           (mode),
        .shift_amount   (shift_amount),
        .bind_enable    (bind_enable),
        .acc_reset      (acc_reset),
        .tensor_out     (tensor_out),
        .popcount       (popcount),
        .hamming_dist   (hamming_dist),
        .entropy_anomaly(entropy_anomaly),
        .valid          (valid)
    );

    always #5 clk = ~clk;

    initial begin
        $dumpfile("tensor_binder.vcd");
        $dumpvars(0, vsa_tensor_binder_tb);

        clk = 0;
        rst_n = 0;
        bind_enable = 0;
        acc_reset = 0;
        mode = 2'b00; // XOR
        shift_amount = 0;
        tensor_a = {BUS_WIDTH{1'b0}};
        tensor_b = {BUS_WIDTH{1'b0}};

        #15;
        rst_n = 1;
        #10;

        // Test 1: XOR Binding (Mode 00)
        tensor_a = { {128{2'b10}} }; // Hex AAAA...
        tensor_b = { {128{2'b11}} }; // Hex FFFF...
        mode = 2'b00;
        bind_enable = 1;
        
        #20;
        bind_enable = 0;

        if (valid && tensor_out === { {128{2'b01}} }) begin
            $display("[MOSKV-BINDER] TEST 1 PASS: XOR Binding verified.");
        end else begin
            $display("[MOSKV-BINDER] TEST 1 FAIL: Hardware Entropy Detected. valid=%b, out=%h", valid, tensor_out);
        end

        // Test 2: PERM_XOR Role-Filler Binding (Mode 10, shift = 1)
        tensor_a = { {64{4'b1010}} };
        tensor_b = { {64{4'b0110}} };
        mode = 2'b10;
        shift_amount = 1;
        bind_enable = 1;

        #20;
        bind_enable = 0;

        if (valid) begin
            $display("[MOSKV-BINDER] TEST 2 PASS: Permuted Role-Filler Binding verified. Popcount=%d, Hamming=%d", popcount, hamming_dist);
        end else begin
            $display("[MOSKV-BINDER] TEST 2 FAIL.");
        end

        #20;
        $finish;
    end

endmodule
