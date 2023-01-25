use std::collections::HashMap;

pub type SimilarityCache = HashMap<(String, Option<isize>, String, Option<isize>), f64>;
