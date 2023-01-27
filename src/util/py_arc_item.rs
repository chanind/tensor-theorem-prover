use pyo3::{prelude::*, PyClass};
use std::sync::Arc;

#[derive(Clone, Hash, PartialEq, Eq, PartialOrd, Ord, Debug)]
pub struct PyArcItem<T>
where
    T: Clone + Ord + PyClass,
{
    // TODO: figure out how to add all the traits and stuff
    // so you don't have to pull this inner set out when using struct
    pub item: Arc<T>,
}
impl<T> PyArcItem<T>
where
    T: Clone + Ord + PyClass,
{
    pub fn new(item: T) -> Self {
        Self {
            item: Arc::new(item),
        }
    }
}

impl<T> From<T> for PyArcItem<T>
where
    T: Clone + Ord + PyClass,
{
    fn from(item: T) -> Self {
        Self {
            item: Arc::new(item.clone()),
        }
    }
}

impl<T> FromPyObject<'_> for PyArcItem<T>
where
    T: Clone + Ord + PyClass,
{
    fn extract(ob: &PyAny) -> PyResult<Self> {
        let item: T = ob.extract()?;
        Ok(PyArcItem::from(item))
    }
}

impl<T> IntoPy<PyObject> for PyArcItem<T>
where
    T: Clone + Ord + PyClass + IntoPy<PyObject>,
{
    fn into_py(self, py: Python) -> PyObject {
        (*self.item).clone().into_py(py)
    }
}
