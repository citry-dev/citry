//! The formatter handles elements nested deeper than a small stack holds.
//!
//! The parser accepts elements nested to any depth, and the formatter's walks
//! over them call themselves once per level. The test runs on a thread with a
//! 256 KiB stack, so a walk without a stack check aborts this test binary.

use citry_template_formatter::format_template;

#[test]
fn deeply_nested_elements_format_on_a_small_stack() {
    let depth = 1_000;
    let elements = "<div>".repeat(depth) + "{{ n }}" + &"</div>".repeat(depth);
    // `c-if` takes its layout from its body, so a chain of them exercises the
    // walk that looks through control tags to the elements inside. That walk
    // starts again at every level, so a shorter chain keeps the test quick
    // while still overflowing the small stack without the guard.
    let control_depth = 250;
    let controls =
        "<c-if cond=\"x\">".repeat(control_depth) + "<p></p>" + &"</c-if>".repeat(control_depth);
    std::thread::Builder::new()
        .stack_size(256 * 1024)
        .spawn(move || {
            for source in [elements, controls] {
                if let Err(error) = format_template(&source) {
                    panic!("{error}");
                }
            }
        })
        .unwrap()
        .join()
        .unwrap();
}
