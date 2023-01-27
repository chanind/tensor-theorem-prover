use std::collections::HashSet;

use crate::types::{Term, Variable};

pub fn find_variables_in_terms(terms: &Vec<&Term>) -> HashSet<Variable> {
    let mut variables = HashSet::new();
    for term in terms {
        match term {
            Term::Variable(variable) => {
                variables.insert(variable.clone());
            }
            Term::BoundFunction(bound_function) => {
                variables.extend(find_variables_in_terms(
                    &bound_function.terms.iter().collect::<Vec<&Term>>(),
                ));
            }
            _ => {}
        }
    }
    variables
}

#[cfg(test)]
mod test {
    use sugars::hset;

    use super::find_variables_in_terms;
    use crate::{
        test_utils::test::{const1, const2, func1, func2, x, y, z},
        types::Term,
    };

    #[test]
    fn test_find_variables_in_terms_with_no_variables() {
        let terms = vec![const1().into(), const2().into()];
        let variables = find_variables_in_terms(&terms.iter().collect());
        assert_eq!(variables, hset! {});
    }

    #[test]
    fn test_find_variables_with_one_variable() {
        let terms: Vec<Term> = vec![const1().into(), x().into()];
        let variables = find_variables_in_terms(&terms.iter().collect());
        assert_eq!(variables, hset! { x() });
    }

    #[test]
    fn test_find_variables_with_repeated_variables() {
        let terms: Vec<Term> = vec![const1().into(), x().into(), x().into(), y().into()];
        let variables = find_variables_in_terms(&terms.iter().collect());
        assert_eq!(variables, hset! { x(), y() });
    }

    #[test]
    fn test_find_variables_in_functions() {
        let terms: Vec<Term> = vec![
            func1().bind(vec![x().into(), y().into()]).into(),
            func2().bind(vec![x().into(), z().into()]).into(),
        ];
        let variables = find_variables_in_terms(&terms.iter().collect());
        assert_eq!(variables, hset! { x(), y(), z() });
    }

    #[test]
    fn test_find_variables_in_nested_functions() {
        let terms: Vec<Term> = vec![func1()
            .bind(vec![
                func2().bind(vec![x().into(), y().into()]).into(),
                z().into(),
            ])
            .into()];
        let variables = find_variables_in_terms(&terms.iter().collect());
        assert_eq!(variables, hset! { x(), y(), z() });
    }
}
