use std::env;

fn main() {
    let limit = env::args()
        .nth(1)
        .expect("expected an iteration count")
        .parse::<u64>()
        .expect("iteration count must be an unsigned integer");
    let total: u64 = (1..=limit).sum();
    println!("{total}");
}
