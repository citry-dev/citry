// Lints we accept for this hand-written parser/compiler: pest's error type is
// large (boxing every Result Err is not worth the churn), the AST enums vary in
// size by design, and a few signatures are inherently wide or complex.
#![allow(clippy::result_large_err)]
#![allow(clippy::large_enum_variant)]
#![allow(clippy::type_complexity)]
#![allow(clippy::too_many_arguments)]
// The `lang::lang` module deliberately shares its parent's name (it holds the
// core LangImpl trait); renaming would ripple through every host-language impl.
#![allow(clippy::module_inception)]
// Doc-comment list indentation is a deliberate style choice here.
#![allow(clippy::doc_overindented_list_items)]

pub mod ast;
pub mod compiler;
pub mod constants;
pub mod error;
pub mod grammar;
pub mod lang {
    pub mod go;
    pub mod js;
    pub mod lang;
    pub mod php;
    pub mod python;
    pub mod rust;
}
pub mod parser;
pub mod parser_context;
pub mod utils {
    pub mod pest;
}

// Re-export the types that users need
pub use crate::ast::{
    Comment, Expr, HtmlAttr, HtmlAttrKind, HtmlEndTag, HtmlStartTag, Node, StaticNamedSlot,
    Template, TemplateElement, Text, Token,
};
pub use crate::error::ParseError;
pub use crate::lang::lang::{Lang, LangImpl, ParseExprResult};
pub use crate::parser::{parse_template, parse_template_with_custom_lang};
pub use crate::parser_context::{ParserContext, TagRules};
