use pyo3::prelude::*;
use pyo3::AsPyPointer;
use std::cmp::Ordering;
use std::collections::BTreeSet;
use std::hash::Hash;
use std::hash::Hasher;

// based on https://stackoverflow.com/a/75135403/245362
fn extract_embedding_ptr(embedding: &Option<Py<PyAny>>) -> Option<isize> {
    if let Some(ref embedding_ref) = embedding {
        Some(embedding_ref.as_ptr() as isize)
    } else {
        None
    }
}

pub trait SimilarityComparable {
    fn similarity_fields(&self) -> (String, &Option<Py<PyAny>>, Option<isize>);

    fn symbol(&self) -> String {
        self.similarity_fields().0
    }
}

#[pyclass(name = "RsPredicate")]
#[derive(Clone, Debug)]
pub struct Predicate {
    #[pyo3(get)]
    pub symbol: String,
    #[pyo3(get)]
    pub embedding: Option<Py<PyAny>>,
    pub embedding_ptr: Option<isize>,
}
#[pymethods]
impl Predicate {
    #[new]
    pub fn new(symbol: &str, embedding: Option<Py<PyAny>>) -> Self {
        let embedding_ptr = extract_embedding_ptr(&embedding);
        Self {
            symbol: symbol.to_string(),
            embedding,
            embedding_ptr,
        }
    }

    pub fn atom(&self, terms: Vec<Term>) -> Atom {
        Atom {
            predicate: self.clone(),
            terms,
        }
    }
}
impl Hash for Predicate {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.symbol.hash(state);
        self.embedding_ptr.hash(state);
    }
}
impl Eq for Predicate {}
impl PartialEq for Predicate {
    fn eq(&self, other: &Self) -> bool {
        self.symbol == other.symbol && self.embedding_ptr == other.embedding_ptr
    }
}
impl Ord for Predicate {
    fn cmp(&self, other: &Self) -> Ordering {
        (&self.symbol, self.embedding_ptr).cmp(&(&other.symbol, other.embedding_ptr))
    }
}
impl PartialOrd for Predicate {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}
impl SimilarityComparable for Predicate {
    fn similarity_fields(&self) -> (String, &Option<Py<PyAny>>, Option<isize>) {
        (self.symbol.clone(), &self.embedding, self.embedding_ptr)
    }
}

#[pyclass(name = "RsConstant")]
#[derive(Clone, Debug)]
pub struct Constant {
    #[pyo3(get)]
    pub symbol: String,
    #[pyo3(get)]
    pub embedding: Option<Py<PyAny>>,
    pub embedding_ptr: Option<isize>,
}
#[pymethods]
impl Constant {
    #[new]
    pub fn new(symbol: &str, embedding: Option<Py<PyAny>>) -> Self {
        let embedding_ptr = extract_embedding_ptr(&embedding);
        Self {
            symbol: symbol.to_string(),
            embedding,
            embedding_ptr,
        }
    }
}
impl Hash for Constant {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.symbol.hash(state);
        self.embedding_ptr.hash(state);
    }
}
impl Eq for Constant {}
impl PartialEq for Constant {
    fn eq(&self, other: &Self) -> bool {
        self.symbol == other.symbol && self.embedding_ptr == other.embedding_ptr
    }
}
impl Ord for Constant {
    fn cmp(&self, other: &Self) -> Ordering {
        (&self.symbol, self.embedding_ptr).cmp(&(&other.symbol, other.embedding_ptr))
    }
}
impl PartialOrd for Constant {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}
impl SimilarityComparable for Constant {
    fn similarity_fields(&self) -> (String, &Option<Py<PyAny>>, Option<isize>) {
        (self.symbol.clone(), &self.embedding, self.embedding_ptr)
    }
}

#[pyclass(name = "RsVariable")]
#[derive(Clone, Hash, PartialEq, Eq, PartialOrd, Ord, Debug)]
pub struct Variable {
    #[pyo3(get)]
    pub name: String,
}
#[pymethods]
impl Variable {
    #[new]
    pub fn new(name: &str) -> Self {
        Self {
            name: name.to_string(),
        }
    }
}

#[pyclass(name = "RsFunction")]
#[derive(Clone, Hash, PartialEq, Eq, PartialOrd, Ord, Debug)]
pub struct Function {
    #[pyo3(get)]
    pub symbol: String,
}
#[pymethods]
impl Function {
    #[new]
    pub fn new(symbol: &str) -> Self {
        Self {
            symbol: symbol.to_string(),
        }
    }

    pub fn bind(&self, terms: Vec<Term>) -> BoundFunction {
        BoundFunction {
            function: self.clone(),
            terms,
        }
    }
}

#[pyclass(name = "RsBoundFunction")]
#[derive(Clone, Hash, PartialEq, Eq, PartialOrd, Ord, Debug)]
pub struct BoundFunction {
    #[pyo3(get)]
    pub function: Function,
    #[pyo3(get)]
    pub terms: Vec<Term>,
}
#[pymethods]
impl BoundFunction {
    #[new]
    pub fn new(function: Function, terms: Vec<Term>) -> Self {
        Self { function, terms }
    }
}

#[derive(FromPyObject, Clone, Hash, PartialEq, Eq, PartialOrd, Ord, Debug)]
pub enum Term {
    Constant(Constant),
    Variable(Variable),
    BoundFunction(BoundFunction),
}
impl IntoPy<PyObject> for Term {
    fn into_py(self, py: Python) -> PyObject {
        match self {
            Term::Constant(c) => c.clone().into_py(py),
            Term::Variable(v) => v.clone().into_py(py),
            Term::BoundFunction(f) => f.clone().into_py(py),
        }
    }
}
impl From<Constant> for Term {
    fn from(c: Constant) -> Self {
        Term::Constant(c)
    }
}
impl From<Variable> for Term {
    fn from(v: Variable) -> Self {
        Term::Variable(v)
    }
}
impl From<BoundFunction> for Term {
    fn from(f: BoundFunction) -> Self {
        Term::BoundFunction(f)
    }
}

#[pyclass(name = "RsAtom")]
#[derive(Clone, Hash, PartialEq, Eq, PartialOrd, Ord, Debug)]
pub struct Atom {
    #[pyo3(get)]
    pub predicate: Predicate,
    #[pyo3(get)]
    pub terms: Vec<Term>,
}
#[pymethods]
impl Atom {
    #[new]
    pub fn new(predicate: Predicate, terms: Vec<Term>) -> Self {
        Self { predicate, terms }
    }
}

#[pyclass(name = "RsCNFLiteral")]
#[derive(Clone, Hash, PartialEq, Eq, PartialOrd, Ord, Debug)]
pub struct CNFLiteral {
    #[pyo3(get)]
    pub atom: Atom,
    #[pyo3(get)]
    pub polarity: bool,
}
#[pymethods]
impl CNFLiteral {
    #[new]
    pub fn new(atom: Atom, polarity: bool) -> Self {
        Self { atom, polarity }
    }
}

#[pyclass(name = "RsCNFDisjunction")]
#[derive(Clone, Hash, PartialEq, Eq, PartialOrd, Ord, Debug)]
pub struct CNFDisjunction {
    #[pyo3(get)]
    pub literals: BTreeSet<CNFLiteral>,
}
#[pymethods]
impl CNFDisjunction {
    #[new]
    pub fn new(literals: BTreeSet<CNFLiteral>) -> Self {
        Self { literals }
    }
}

pub fn register_python_symbols(_py: Python<'_>, module: &PyModule) -> PyResult<()> {
    module.add_class::<Predicate>()?;
    module.add_class::<Constant>()?;
    module.add_class::<Variable>()?;
    module.add_class::<Function>()?;
    module.add_class::<BoundFunction>()?;
    module.add_class::<Atom>()?;
    module.add_class::<CNFLiteral>()?;
    module.add_class::<CNFDisjunction>()?;
    Ok(())
}
