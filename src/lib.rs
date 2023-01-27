#[macro_use]
extern crate lazy_static;

use pyo3::prelude::*;

mod prover;
mod test_utils;
mod types;
mod util;

#[pymodule]
fn _rust(py: Python<'_>, m: &PyModule) -> PyResult<()> {
    types::register_python_symbols(py, m)?;
    prover::register_python_symbols(py, m)?;
    Ok(())
}
