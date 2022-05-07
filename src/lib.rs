use std::path::Path;

fn range2vec8(lbi: u8, ubi: u8) -> Vec<u8> {
    (lbi..=ubi).collect()
}

fn new_u8_vec_generator(lbi: u8) -> impl Fn(u8) -> Vec<u8> {
    move |ubi: u8| range2vec8(lbi, ubi)
}

fn new_month_generator() -> impl Fn() -> Vec<u8> {
    let gen = new_u8_vec_generator(1);
    move || gen(12)
}

fn new_day_generator() -> impl Fn() -> Vec<u8> {
    let gen = new_u8_vec_generator(1);
    move || gen(31)
}

fn new_counter<C>(checker: C) -> impl Fn(i32) -> i32
where
    C: Fn(i32, u8, u8) -> bool,
{
    let mgen = new_month_generator();
    let dgen = new_day_generator();
    move |year: i32| {
        let month_iter = mgen().into_iter();
        month_iter.fold(0, |tot: i32, month: u8| {
            let day_iter = dgen().into_iter();
            let checked = day_iter.filter(|&day: &u8| checker(year, month, day));
            let count: usize = checked.count();
            tot.checked_add(count as i32).unwrap_or(tot)
        })
    }
}

fn new_fs_path_checker<P>(base: P) -> impl Fn(i32, u8, u8) -> bool
where
    P: AsRef<Path>,
{
    move |year: i32, month: u8, day: u8| {
        let joined = base
            .as_ref()
            .join(format!("{:04}/{:02}/{:02}", year, month, day));
        joined.exists()
    }
}

fn new_fs_env_base_getter(key: &str, alt: &str) -> impl Fn() -> String {
    let a: String = alt.into();
    let k: String = key.into();
    move || std::env::var(k.as_str()).unwrap_or_else(|_| a.clone())
}

#[no_mangle]
pub extern "C" fn count_ymd(year: i32) -> i32 {
    let fs_base_getter = new_fs_env_base_getter("ENV_BASE_PATH", "/guest.d");
    let base: String = fs_base_getter();

    let checker = new_fs_path_checker(base);
    let counter = new_counter(checker);
    counter(year)
}
