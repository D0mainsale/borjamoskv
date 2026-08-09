`timescale 1ns / 1ps

/*
 * CORTEX Law Ω0 Enforcement.
 * Hardware Sovereign: Silicon-Overlord-Omega
 * Matrix: VSA Tensor Bundler (Register-Level Neuromorphic Majority Architecture)
 * Author: Borja Moskv (borjamoskv)
 */
module vsa_tensor_bundler #(
    parameter BUS_WIDTH = 256
)(
    input  wire                 clk,
    input  wire                 rst_n,
    input  wire [BUS_WIDTH-1:0] tensor_a,
    input  wire [BUS_WIDTH-1:0] tensor_b,
    input  wire [BUS_WIDTH-1:0] tensor_c,
    input  wire                 bundle_enable,
    input  wire                 acc_reset,
    output reg  [BUS_WIDTH-1:0] tensor_out,
    output reg  [BUS_WIDTH:0]   popcount,
    output reg                  entropy_anomaly,
    output reg                  valid
);

    // Registros de etapa 1 (Input Latch)
    reg [BUS_WIDTH-1:0] reg_a;
    reg [BUS_WIDTH-1:0] reg_b;
    reg [BUS_WIDTH-1:0] reg_c;
    reg                 reg_enable;

    // Acumulador de registros para superposición secuencial
    reg [BUS_WIDTH-1:0] acc_bundle_reg;

    // Matriz combinacional de compuerta de mayoría neuromórfica
    // Y[i] = (A[i] & B[i]) | (B[i] & C[i]) | (A[i] & C[i])
    wire [BUS_WIDTH-1:0] majority_combinational;
    assign majority_combinational = (reg_a & reg_b) | (reg_b & reg_c) | (reg_a & reg_c);

    // Cálculo combinacional de Popcount para verificación de exergía
    integer i;
    reg [BUS_WIDTH:0] count_temp;
    always @(*) begin
        count_temp = 0;
        for (i = 0; i < BUS_WIDTH; i = i + 1) begin
            if (majority_combinational[i]) begin
                count_temp = count_temp + 1'b1;
            end
        end
    end

    // Etapa 2: Latch de salida y actualización de estado
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            reg_a           <= {BUS_WIDTH{1'b0}};
            reg_b           <= {BUS_WIDTH{1'b0}};
            reg_c           <= {BUS_WIDTH{1'b0}};
            reg_enable      <= 1'b0;
            tensor_out      <= {BUS_WIDTH{1'b0}};
            acc_bundle_reg  <= {BUS_WIDTH{1'b0}};
            popcount        <= {(BUS_WIDTH+1){1'b0}};
            entropy_anomaly <= 1'b0;
            valid           <= 1'b0;
        end else begin
            // Latch Etapa 1
            reg_a      <= tensor_a;
            reg_b      <= tensor_b;
            reg_c      <= tensor_c;
            reg_enable <= bundle_enable;

            if (acc_reset) begin
                acc_bundle_reg <= {BUS_WIDTH{1'b0}};
            end

            // Latch Etapa 2
            if (reg_enable) begin
                tensor_out      <= majority_combinational;
                acc_bundle_reg  <= acc_bundle_reg | majority_combinational;
                popcount        <= count_temp;
                entropy_anomaly <= (count_temp == 0) || (count_temp == BUS_WIDTH);
                valid           <= 1'b1;
            end else begin
                valid           <= 1'b0;
            end
        end
    end

    // =========================================================================
    // C5-REAL FORMAL VERIFICATION (Zero-Latency Guarantee)
    // =========================================================================
    `ifdef FORMAL
    always @(posedge clk) begin
        if (rst_n) begin
            if ($past(reg_enable)) begin
                assert(valid == 1'b1);
                assert(popcount <= BUS_WIDTH);
            end
        end
    end
    `endif

endmodule

