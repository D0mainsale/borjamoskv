use rayon::prelude::*;
use std::collections::HashSet;
use std::ffi::{CStr, CString};
use std::os::raw::c_char;
use std::ptr;

#[no_mangle]
pub extern "C" fn jaccard_similarity_rust(
    a_tokens: *const *const c_char,
    a_len: usize,
    b_tokens: *const *const c_char,
    b_len: usize,
) -> f64 {
    let set_a = unsafe {
        (0..a_len)
            .map(|i| CStr::from_ptr(*a_tokens.add(i)).to_string_lossy().into_owned())
            .collect::<HashSet<String>>()
    };
    let set_b = unsafe {
        (0..b_len)
            .map(|i| CStr::from_ptr(*b_tokens.add(i)).to_string_lossy().into_owned())
            .collect::<HashSet<String>>()
    };

    if set_a.is_empty() && set_b.is_empty() {
        return 0.0;
    }
    let intersection = set_a.intersection(&set_b).count();
    let union = set_a.len() + set_b.len() - intersection;
    if union == 0 {
        0.0
    } else {
        intersection as f64 / union as f64
    }
}

#[repr(C)]
pub struct MatchResult {
    pub name_i: *mut c_char,
    pub name_j: *mut c_char,
    pub similarity: f64,
}

#[no_mangle]
pub extern "C" fn detect_duplicates_ptr(
    names: *const *const c_char,
    tokens_ptrs: *const *const *const c_char,
    tokens_lens: *const usize,
    count: usize,
    threshold: f64,
    out_matches: *mut *mut MatchResult,
    out_count: *mut usize,
) {
    let profiles: Vec<(String, HashSet<String>)> = unsafe {
        (0..count)
            .map(|i| {
                let name = CStr::from_ptr(*names.add(i)).to_string_lossy().into_owned();
                let len = *tokens_lens.add(i);
                let ptrs = *tokens_ptrs.add(i);
                let tokens = (0..len)
                    .map(|j| CStr::from_ptr(*ptrs.add(j)).to_string_lossy().into_owned())
                    .collect::<HashSet<String>>();
                (name, tokens)
            })
            .collect()
    };

    let mut matches = Vec::new();
    for i in 0..count {
        for j in (i + 1)..count {
            let intersection = profiles[i].1.intersection(&profiles[j].1).count();
            let union = profiles[i].1.len() + profiles[j].1.len() - intersection;
            let sim = if union > 0 { intersection as f64 / union as f64 } else { 0.0 };

            if sim >= threshold {
                matches.push(MatchResult {
                    name_i: CString::new(profiles[i].0.clone()).unwrap().into_raw(),
                    name_j: CString::new(profiles[j].0.clone()).unwrap().into_raw(),
                    similarity: sim,
                });
            }
        }
    }

    unsafe {
        *out_count = matches.len();
        let size = matches.len() * std::mem::size_of::<MatchResult>();
        let ptr = std::alloc::alloc(std::alloc::Layout::from_size_align(size, 8).unwrap()) as *mut MatchResult;
        ptr::copy_nonoverlapping(matches.as_ptr(), ptr, matches.len());
        *out_matches = ptr;
        std::mem::forget(matches); // Prevent cleanup of the raw pointers inside
    }
}

#[no_mangle]
pub extern "C" fn vsa_bind_rust(a: *const u8, b: *const u8, out: *mut u8, len: usize) {
    let a_slice = unsafe { std::slice::from_raw_parts(a, len) };
    let b_slice = unsafe { std::slice::from_raw_parts(b, len) };
    let out_slice = unsafe { std::slice::from_raw_parts_mut(out, len) };
    
    for i in 0..len {
        out_slice[i] = a_slice[i] ^ b_slice[i];
    }
}

#[no_mangle]
pub extern "C" fn vsa_popcount_rust(a: *const u8, len: usize) -> usize {
    let a_slice = unsafe { std::slice::from_raw_parts(a, len) };
    a_slice.iter().map(|&x| x.count_ones() as usize).sum()
}

use std::fs::OpenOptions;
use std::io::Write;
use std::time::{SystemTime, UNIX_EPOCH};

#[no_mangle]
pub extern "C" fn flight_recorder_append_rust(
    session_id: *const c_char,
    step_type: *const c_char,
    hash_payload: *const c_char,
) -> bool {
    let session = unsafe { CStr::from_ptr(session_id).to_string_lossy() };
    let step = unsafe { CStr::from_ptr(step_type).to_string_lossy() };
    let payload = unsafe { CStr::from_ptr(hash_payload).to_string_lossy() };

    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis();

    let record = format!("[{}] {} | {} | {}\n", timestamp, session, step, payload);

    let mut file = match OpenOptions::new()
        .create(true)
        .append(true)
        .open("/tmp/cortex_blackbox.wal")
    {
        Ok(f) => f,
        Err(_) => return false,
    };

    if file.write_all(record.as_bytes()).is_ok() {
        // Sync to OS cache / disk immediately
        file.sync_data().is_ok()
    } else {
        false
    }
}

// C5-REAL | Ultrathin RPC Node FFI (Zero-Latency Mandate)
use reqwest::Client;
use serde_json::json;
use std::env;
use std::time::Duration;

pub struct UltrathinRpc {
    nodes: Vec<String>,
    client: Client,
}

impl UltrathinRpc {
    pub fn new() -> Self {
        let mut nodes = vec![
            "https://ethereum-rpc.publicnode.com".to_string(),
            "https://eth.drpc.org".to_string(),
        ];
        
        if let Ok(alchemy) = env::var("ALCHEMY_URL_ETH_MAINNET") {
            nodes.push(alchemy);
        }

        UltrathinRpc {
            nodes,
            client: Client::builder()
                .timeout(Duration::from_secs(2))
                .build()
                .expect("ERROR [C4]: Fallo al crear el socket HTP/TLS."),
        }
    }

    pub async fn get_block_number(&self) -> Result<(u64, String), String> {
        let payload = json!({
            "jsonrpc": "2.0",
            "method": "eth_blockNumber",
            "params": [],
            "id": 1
        });

        for url in &self.nodes {
            match self.client.post(url).json(&payload).send().await {
                Ok(res) => {
                    if let Ok(json) = res.json::<serde_json::Value>().await {
                        if let Some(result_hex) = json.get("result").and_then(|r| r.as_str()) {
                            let clean_hex = result_hex.trim_start_matches("0x");
                            if let Ok(block_num) = u64::from_str_radix(clean_hex, 16) {
                                return Ok((block_num, url.to_string()));
                            }
                        }
                    }
                }
                Err(_) => continue,
            }
        }
        
        Err("ERROR [C4]: Colapso Total RPC. Cero nodos disponibles.".to_string())
    }
}

// Extern C bridge for Python Cortex Daemon
#[no_mangle]
pub extern "C" fn fetch_ultrathin_rpc_block() -> u64 {
    let rt = tokio::runtime::Runtime::new().unwrap();
    rt.block_on(async {
        let rpc = UltrathinRpc::new();
        match rpc.get_block_number().await {
            Ok((block, _)) => block,
            Err(_) => 0 // 0 indica Colapso (C4)
        }
    })
}

// AUTODIDACT-Ω C5-REAL Bridge
use sha2::{Sha256, Digest};
use memmap2::MmapMut;

#[no_mangle]
pub extern "C" fn crystallize_skill(ast_ptr: *const u8, len: usize, output_hash: *mut u8) -> i32 {
    if ast_ptr.is_null() || output_hash.is_null() {
        return -1; // [FATAL] Null pointer interception
    }

    // 1. O(1) Memory mapped ingestion
    let ast_buffer = unsafe { std::slice::from_raw_parts(ast_ptr, len) };

    // 2. Epistemic Breaker (Hardware level check proxy)
    // Redundant execution halt logic goes here.

    // 3. VSA Ledger Sealing (SHA256 mathematical lock)
    let mut hasher = Sha256::new();
    hasher.update(ast_buffer);
    let result = hasher.finalize();

    // 4. Write back to output tensor buffer
    unsafe {
        let output_slice = std::slice::from_raw_parts_mut(output_hash, 32);
        output_slice.copy_from_slice(&result);
    }

    0 // SUCCESS
}
