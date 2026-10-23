//! Level C2 of the native render path: read every row of a call run's loop
//! in one call. The design and every error mode are in
//! `docs/design/native_render.md`.
//!
//! A call run is the rows one `c-for` places at one component call site,
//! such as `<c-Row c-for="row in phase['outputs']" #c-key="row['id']"
//! c-row="row" />`. Python's walk of such a loop evaluates the iterable
//! once, then for each row evaluates the call's inputs and its key. When
//! each of those expressions is a plain path (a name followed by constant
//! subscripts), reading it runs no template or user code as long as every
//! container on the way is an exact `dict`, `list` or `tuple`, with one
//! exception: a dict lookup runs `__eq__` on a stored key whose hash equals
//! the key looked up. This module holds the part of that read that needs no
//! Python:
//!
//! - [`WalkPlan::new`] checks the paths Python built from the template's
//!   expressions ([`WalkSpec`]) and numbers their steps, so the PyO3 layer
//!   can build one Python key object per step, once;
//! - [`WalkPlan::read_rows`] reads every row over any [`Tree`], in the order
//!   Python's walk reads them: the iterable, then for each row each input in
//!   attribute order, then the key. It returns the values it read (the
//!   caller's own handles, never copies) or the reason it declines. A decline
//!   sends the loop back to Python's walk, which raises its own error, with
//!   its template position, when a read fails.
//!
//! Which reads are allowed is decided by exact type, as Python's evaluator
//! would see them: a constant subscript of an exact `dict` (by a `str` or
//! `int` key), or a non-negative constant index of an exact `list` or
//! `tuple`. A row's key must be an exact `str`, or an exact `int` within
//! `i64`, whose decimal text stays far below Python's digit limit. Anything
//! else declines.

/// One constant subscript of a path, as written in the template.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum StepKey {
    /// `x['name']`.
    Str(String),
    /// `x[3]`; [`WalkPlan::new`] refuses a negative one, because Python
    /// counts it from the end.
    Int(i64),
}

/// A path as Python lowered it: a name, then constant subscripts.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PathSpec {
    /// The name the path starts from: the loop variable or a name in scope.
    pub name: String,
    pub steps: Vec<StepKey>,
}

/// What Python lowered from one loop: `<target> in <iterable>`, the call's
/// inputs in attribute order, and its `#c-key`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct WalkSpec {
    pub target: String,
    pub iterable: PathSpec,
    pub kwargs: Vec<PathSpec>,
    pub key: PathSpec,
}

/// Why a [`WalkSpec`] cannot become a plan. Python's lowering never passes
/// such a spec; the checks keep a wrong one from reading something else.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum WalkPlanError {
    /// The iterable starts from the loop variable, which is not in scope
    /// while the iterable is evaluated.
    IterableReadsTarget,
    /// A name or key starting with `_`, which the expression sandbox refuses.
    PrivateName(String),
    /// A negative index (Python counts it from the end).
    NegativeIndex(i64),
    /// An empty name.
    EmptyName,
}

/// One numbered subscript of a plan. The number is the step's position in
/// [`WalkPlan::steps`], so a caller can keep one prepared key per step.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Step {
    pub id: usize,
    pub key: StepKey,
}

/// Where a path starts.
#[derive(Clone, Debug, PartialEq, Eq)]
enum Root {
    /// The loop variable: the row's own item.
    Target,
    /// A name in the loop's scope, looked up with the step of this id.
    Scope(usize),
}

#[derive(Clone, Debug)]
struct Path {
    root: Root,
    steps: Vec<Step>,
}

/// The kind of a value, by its exact type, as far as the walk cares.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Shape {
    /// An exact `dict`.
    Dict,
    /// An exact `list` or `tuple`.
    Seq,
    /// An exact `str`.
    Str,
    /// An exact `int` within `i64` (never `bool`).
    Int(i64),
    /// Citry's `Const` marker. When a row's item is one, Python's row scope
    /// (`_overlay_const_mapping`) replaces it with the plain value it wraps,
    /// which the walk does not do, so it declines.
    Marker,
    /// Anything else.
    Other,
}

/// A value the walk can read, implemented by the PyO3 layer over Python
/// objects (and by the tests over JSON).
pub trait Tree: Sized {
    /// An error the read itself raised (in Python, a dict lookup can run a
    /// colliding key's `__eq__`). The caller decides what to do with it.
    type Error;
    fn shape(&self) -> Shape;
    /// `self[key]` for a `Dict`; `Ok(None)` when the key is missing.
    fn get(&self, step: &Step) -> Result<Option<Self>, Self::Error>;
    /// Item `index` of a `Seq`, or None at or past its current end.
    fn item(&self, index: usize) -> Option<Self>;
    /// A hint for how many items a `Seq` has now, used only to reserve room.
    fn len_hint(&self) -> usize;
}

/// Why [`WalkPlan::read_rows`] declined. Python's walk then runs the loop.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Decline {
    /// The loop's variables are not a dict.
    Scope,
    /// The iterable is not an exact list or tuple.
    Iterable,
    /// A name or key is missing, or an index is past the end.
    Missing,
    /// A container on a path has another type, or a list is read by a str key.
    NotPlain,
    /// A row's item is a `Const` marker.
    Marker,
    /// A row's key is not an exact str or an int within i64.
    KeyType,
}

impl Decline {
    /// The reason's name, as the PyO3 layer returns it to Python.
    pub fn as_str(self) -> &'static str {
        match self {
            Decline::Scope => "scope",
            Decline::Iterable => "iterable",
            Decline::Missing => "missing",
            Decline::NotPlain => "not_plain",
            Decline::Marker => "marker",
            Decline::KeyType => "key_type",
        }
    }
}

/// A row's key as read: the str value itself, or an int to write in decimal.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum RowKey<T> {
    Str(T),
    Int(i64),
}

/// Every row's values: `kwargs` holds `kwargs_len` values per row, row after
/// row, in attribute order.
pub struct Rows<T> {
    pub len: usize,
    pub kwargs_len: usize,
    pub kwargs: Vec<T>,
    pub keys: Vec<RowKey<T>>,
}

impl<T> Rows<T> {
    /// Row `index`'s input values, in attribute order.
    pub fn row_kwargs(&self, index: usize) -> &[T] {
        &self.kwargs[index * self.kwargs_len..][..self.kwargs_len]
    }
}

/// A checked [`WalkSpec`] with numbered steps.
#[derive(Clone, Debug)]
pub struct WalkPlan {
    steps: Vec<Step>,
    iterable: Path,
    kwargs: Vec<Path>,
    key: Path,
}

impl WalkPlan {
    /// Check `spec` and number its steps: first each distinct scope name,
    /// in order of first use, then each path's subscripts.
    pub fn new(spec: &WalkSpec) -> Result<Self, WalkPlanError> {
        check_name(&spec.target)?;
        if spec.iterable.name == spec.target {
            return Err(WalkPlanError::IterableReadsTarget);
        }
        // The scope names come first, so a scope name's position in
        // `scope_names` is also its step id, which `Root::Scope` relies on.
        let mut scope_names: Vec<String> = Vec::new();
        for path in [&spec.iterable]
            .into_iter()
            .chain(&spec.kwargs)
            .chain([&spec.key])
        {
            check_name(&path.name)?;
            if path.name != spec.target && !scope_names.contains(&path.name) {
                scope_names.push(path.name.clone());
            }
        }
        let mut steps: Vec<Step> = scope_names
            .iter()
            .enumerate()
            .map(|(id, name)| Step {
                id,
                key: StepKey::Str(name.clone()),
            })
            .collect();
        let mut number = |path: &PathSpec| -> Result<Path, WalkPlanError> {
            let root = if path.name == spec.target {
                Root::Target
            } else {
                // Every scope name was collected above, so the lookup always
                // finds it; the error only satisfies the type.
                let position = scope_names.iter().position(|name| *name == path.name);
                Root::Scope(position.ok_or(WalkPlanError::EmptyName)?)
            };
            let mut numbered = Vec::with_capacity(path.steps.len());
            for key in &path.steps {
                match key {
                    StepKey::Str(text) if text.starts_with('_') => {
                        return Err(WalkPlanError::PrivateName(text.clone()));
                    }
                    StepKey::Int(index) if *index < 0 => {
                        return Err(WalkPlanError::NegativeIndex(*index));
                    }
                    _ => {}
                }
                let step = Step {
                    id: steps.len(),
                    key: key.clone(),
                };
                steps.push(step.clone());
                numbered.push(step);
            }
            Ok(Path {
                root,
                steps: numbered,
            })
        };
        let iterable = number(&spec.iterable)?;
        let kwargs = spec
            .kwargs
            .iter()
            .map(&mut number)
            .collect::<Result<Vec<_>, _>>()?;
        let key = number(&spec.key)?;
        Ok(WalkPlan {
            steps,
            iterable,
            kwargs,
            key,
        })
    }

    /// Every step, by id: the scope names first, then each subscript.
    pub fn steps(&self) -> &[Step] {
        &self.steps
    }

    /// How many inputs each row has.
    pub fn kwargs_len(&self) -> usize {
        self.kwargs.len()
    }

    /// Read every row from `scope` (the loop's variables, a `Dict`), in the
    /// order Python's walk reads them; see the module docs.
    ///
    /// `Ok(Err(decline))` sends the loop back to Python; `Err(error)` is an
    /// error a read raised, which the caller handles.
    pub fn read_rows<T: Tree + Clone>(
        &self,
        scope: &T,
    ) -> Result<Result<Rows<T>, Decline>, T::Error> {
        if scope.shape() != Shape::Dict {
            return Ok(Err(Decline::Scope));
        }
        // The iterable is evaluated once, before any row.
        let iterable = match self.read_path(&self.iterable, scope, None)? {
            Ok(value) => value,
            Err(decline) => return Ok(Err(decline)),
        };
        if iterable.shape() != Shape::Seq {
            return Ok(Err(Decline::Iterable));
        }
        let hint = iterable.len_hint();
        let mut rows = Rows {
            len: 0,
            kwargs_len: self.kwargs.len(),
            kwargs: Vec::with_capacity(hint * self.kwargs.len()),
            keys: Vec::with_capacity(hint),
        };
        // Python's list iterator checks the length before every item, so a
        // list that a colliding key's `__eq__` grows or shrinks during the
        // reads is followed the same way here.
        while let Some(item) = iterable.item(rows.len) {
            if item.shape() == Shape::Marker {
                return Ok(Err(Decline::Marker));
            }
            for path in &self.kwargs {
                match self.read_path(path, scope, Some(&item))? {
                    Ok(value) => rows.kwargs.push(value),
                    Err(decline) => return Ok(Err(decline)),
                }
            }
            let key = match self.read_path(&self.key, scope, Some(&item))? {
                Ok(value) => value,
                Err(decline) => return Ok(Err(decline)),
            };
            rows.keys.push(match key.shape() {
                Shape::Str => RowKey::Str(key),
                Shape::Int(number) => RowKey::Int(number),
                _ => return Ok(Err(Decline::KeyType)),
            });
            rows.len += 1;
        }
        Ok(Ok(rows))
    }

    /// Read one path from the row's item (the loop variable) or the scope.
    ///
    /// A scope name is looked up for every path that reads it, as Python's
    /// evaluator looks it up for every expression of every row, so the
    /// lookups (and any colliding key's `__eq__`) happen as often as there.
    fn read_path<T: Tree + Clone>(
        &self,
        path: &Path,
        scope: &T,
        item: Option<&T>,
    ) -> Result<Result<T, Decline>, T::Error> {
        let mut value = match path.root {
            Root::Target => match item {
                Some(item) => item.clone(),
                None => return Ok(Err(Decline::Missing)),
            },
            Root::Scope(id) => match scope.get(&self.steps[id])? {
                Some(found) => found,
                None => return Ok(Err(Decline::Missing)),
            },
        };
        for step in &path.steps {
            let next = match (value.shape(), &step.key) {
                (Shape::Dict, _) => value.get(step)?,
                // `new` refused negative indexes, so the conversion holds.
                (Shape::Seq, StepKey::Int(index)) => match usize::try_from(*index) {
                    Ok(index) => value.item(index),
                    Err(_) => return Ok(Err(Decline::Missing)),
                },
                _ => return Ok(Err(Decline::NotPlain)),
            };
            match next {
                Some(next) => value = next,
                None => return Ok(Err(Decline::Missing)),
            }
        }
        Ok(Ok(value))
    }
}

fn check_name(name: &str) -> Result<(), WalkPlanError> {
    if name.is_empty() {
        return Err(WalkPlanError::EmptyName);
    }
    if name.starts_with('_') {
        return Err(WalkPlanError::PrivateName(name.to_owned()));
    }
    Ok(())
}
