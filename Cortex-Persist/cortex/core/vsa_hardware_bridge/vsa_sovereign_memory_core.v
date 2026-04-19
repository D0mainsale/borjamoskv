`timescale 1ns / 1ps

/*
 * CORTEX Law Ω0 & Ω9 Enforcement.
 * Hardware Sovereign: Silicon-Overlord-Omega
 * Matrix: VSA True Kanerva SDM Array + LFSR Ebbinghaus Decay
 * Aniquila la simulacion C4 estructurada en `retrieve_sovereign_memory` 
 * y mapea el `enforce_decay` O(1) a Direct-Silicon.
 */
module vsa_sovereign_memory_core #(
    parameter BUS_WIDTH = 256,
    parameter MEM_DEPTH = 32, // Escala geometrica para JIT Synthesis (Registros)
    parameter THRESHOLD = 16 
)(
    input  wire                 clk,
    input  wire                 rst_n,
    input  wire                 search_enable,
    input  wire                 decay_enable,  // Pulso de desgaste ebbinghaus
    input  wire [BUS_WIDTH-1:0] query_tensor,
    output reg  [BUS_WIDTH-1:0] retrieved_tensor,
    output reg                  valid_hit
);

    // 1. Matriz Local SDM (DRAM/BlockRAM/FFs)
    reg [BUS_WIDTH-1:0] mem_matrix [0:MEM_DEPTH-1];
    
    // 2. LFSR - Motor de decaimiento Ebbinghaus (PRNG)
    reg [BUS_WIDTH-1:0] lfsr;

    // Combinacionales de distancia
    wire [BUS_WIDTH-1:0] dist_diff [0:MEM_DEPTH-1];
    integer i, j;
    reg [8:0] pop_counts [0:MEM_DEPTH-1]; // log2(256)=8 + 1
    reg [BUS_WIDTH-1:0] best_tensor;
    reg hit_flag;

    // Computacion Combinacional O(1)
    always @* begin
        hit_flag = 1'b0;
        best_tensor = {BUS_WIDTH{1'b0}};
        
        // Broadcast de la distancia de Hamming sobre todos los nodos de memoria simultaneamente
        for (i = 0; i < MEM_DEPTH; i = i + 1) begin
            dist_diff[i] = mem_matrix[i] ^ query_tensor;
            pop_counts[i] = 0;
            for (j = 0; j < BUS_WIDTH; j = j + 1) begin
                pop_counts[i] = pop_counts[i] + dist_diff[i][j];
            end
            
            // Logica de deteccion de Hard Location (Dentro del perimetro Kanerva)
            if (pop_counts[i] <= THRESHOLD && !hit_flag) begin
                best_tensor = mem_matrix[i];
                hit_flag = 1'b1;
            end
        end
    end

    // Clocked Logic / Mutacion de Silicio
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            lfsr <= {BUS_WIDTH{1'b1}}; // Non-zero seed inicial
            valid_hit <= 1'b0;
            retrieved_tensor <= {BUS_WIDTH{1'b0}};
        end else begin
            // LFSR Bit Shift Galoico
            lfsr <= {lfsr[BUS_WIDTH-2:0], lfsr[BUS_WIDTH-1] ^ lfsr[0]};

            if (search_enable) begin
                retrieved_tensor <= best_tensor;
                valid_hit <= hit_flag;
            end else begin
                valid_hit <= 1'b0;
            end

            // Ebbinghaus Decay Activo = Ruido Inyectado Estocasticamente en L1
            if (decay_enable) begin
                for (i = 0; i < MEM_DEPTH; i = i + 1) begin
                    // Flipa el tensor local donde el pulso LFSR sea 1, disolviendo el contexto poco a poco
                    mem_matrix[i] <= mem_matrix[i] ^ lfsr;
                end
            end
        end
    end

endmodule
