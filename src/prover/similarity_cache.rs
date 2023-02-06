use std::hash::BuildHasherDefault;

use dashmap::DashMap;
use rustc_hash::FxHasher;

pub type SimilarityCache = DashMap<u64, f64, BuildHasherDefault<FxHasher>>;
