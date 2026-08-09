`timescale 1ns / 1ps

/*
 * CORTEX Law Ω0 Enforcement.
 * Testbench for VSA Tensor Bundler (Neuromorphic Majority Superposition - Register Level)
 * Author: Borja Moskv (borjamoskv)
 */
module vsa_tensor_bundler_tb;

    parameter BUS_WIDTH = 256;

    reg                  clk;
    reg                  rst_n;
    reg  [BUS_WIDTH-1:0] tensor_a;
    reg  [BUS_WIDTH-1:0] tensor_b;
    reg  [BUS_WIDTH-1:0] tensor_c;
    reg                  bundle_enable;
    reg                  acc_reset;

    wire [BUS_WIDTH-1:0] tensor_out;
    wire [BUS_WIDTH:0]   popcount;
    wire                 entropy_anomaly;
    wire                 valid;

    vsa_tensor_bundler #(
        .BUS_WIDTH(BUS_WIDTH)
    ) dut (
        .clk          (clk),
        .rst_n        (rst_n),
        .tensor_a     (tensor_a),
        .tensor_b     (tensor_b),
        .tensor_c     (tensor_c),
        .bundle_enable(bundle_enable),
        .acc_reset    (acc_reset),
        .tensor_out   (tensor_out),
        .popcount     (popcount),
        .entropy_anomaly (entropy_anomaly),
        .valid        (valid)
    );

    always #5 clk = ~clk;

    initial begin
        $dumpfile("tensor_bundler.vcd");
        $dumpvars(0, vsa_tensor_bundler_tb);

        clk = 0;
        rst_n = 0;
        bundle_enable = 0;
        acc_reset = 0;
        tensor_a = {BUS_WIDTH{1'b0}};
        tensor_b = {BUS_WIDTH{1'b0}};
        tensor_c = {BUS_WIDTH{1'b0}};

        #15;
        rst_n = 1;
        #10;

        // Test Vector 1: Majority voting logic
        tensor_a = { {64{4'b1111}} };
        tensor_b = { {64{4'b1100}} };
        tensor_c = { {64{4'b1010}} };
        bundle_enable = 1;

        #20; // 2 ciclos de reloj para pasar por el pipeline de registros
        bundle_enable = 0;

        if (valid && tensor_out === { {64{4'b1110}} }) begin
            $display("[MOSKV-BUNDLER] VALIDATION PASS: Majority gate superposition verified in Register Pipeline.");
        end else begin
            $display("[MOSKV-BUNDLER] VALIDATION FAIL: Hardware Entropy Detected. valid=%b, out=%h", valid, tensor_out);
        end

        #20;
        $finish;
    end

endmodule

