/// Test helpers to make it easier to create and use types in tests and deal with python/numpy
#[cfg(test)]
pub mod test {
    use pyo3::prelude::*;

    use crate::types::{Constant, Function, Predicate, Variable};

    // based on sugar::hmap
    #[macro_export]
    macro_rules! fxmap {
        () => { ::rustc_hash::FxHashMap::default() };

        ( $($key: expr => $value: expr),+ $(,)? ) => {{
                let mut map = ::rustc_hash::FxHashMap::default();
                $(
                    let _ = map.insert($key, $value);
                )+
                map
        }};
    }

    #[macro_export]
    macro_rules! fxset {
        () => { ::rustc_hash::FxHashSet::default() };

        ( $($elem: expr),+ $(,)? ) => {{
            let mut set = ::rustc_hash::FxHashSet::default();
            $(
                set.insert($elem);
            )+
            set
        }};
    }

    pub fn pred1() -> Predicate {
        Predicate::new("pred1", None)
    }
    pub fn pred2() -> Predicate {
        Predicate::new("pred2", None)
    }

    pub fn const1() -> Constant {
        Constant::new("const1", None)
    }
    pub fn const2() -> Constant {
        Constant::new("const2", None)
    }

    pub fn func1() -> Function {
        Function::new("func1")
    }
    pub fn func2() -> Function {
        Function::new("func2")
    }

    pub fn x() -> Variable {
        Variable::new("X")
    }
    pub fn y() -> Variable {
        Variable::new("Y")
    }
    pub fn z() -> Variable {
        Variable::new("Z")
    }
    pub fn a() -> Variable {
        Variable::new("A")
    }
    pub fn b() -> Variable {
        Variable::new("B")
    }
    pub fn c() -> Variable {
        Variable::new("C")
    }

    pub fn to_numpy_array(vec: Vec<f64>) -> PyObject {
        pyo3::prepare_freethreaded_python();
        let py_res: PyResult<PyObject> = Python::with_gil(|py| {
            let numpy = PyModule::import(py, "numpy")?;
            let array: PyObject = numpy.getattr("array")?.into();
            array.call1(py, (vec,))
        });
        py_res.expect("Unable to convert vec to numpy array")
    }

    /// Copied from similarity.py, because I can't figure out how to directly import this in ruse
    pub fn get_py_similarity_fn() -> PyObject {
        pyo3::prepare_freethreaded_python();
        let py_res: PyResult<PyObject> = Python::with_gil(|py| {
            let similarity_mod = PyModule::from_code(
                py,
                r#"
import numpy as np
from numpy.linalg import norm

def symbol_compare(item1, item2):
    return 1.0 if item1.symbol == item2.symbol else 0.0

def cosine_similarity(item1, item2):
    if item1.embedding is None or item2.embedding is None:
        return symbol_compare(item1, item2)
    return np.dot(item1.embedding, item2.embedding) / (
        norm(item1.embedding) * norm(item2.embedding)
    )
                "#,
                "",
                "",
            );
            Ok(similarity_mod?.getattr("cosine_similarity")?.into())
        });
        py_res.expect("Unable to load py cosine similarity")
    }
}
