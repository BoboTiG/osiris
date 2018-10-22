#!bin/bash


show_all() {
    # Print all time actions counts.

    local sql

    sql="\
  SELECT action, SUM(count) \
    FROM osiris \
GROUP BY action \
;"

    sqlite3 -readonly statistics.db "${sql}"
}

show() {
    # Print actions counts day by day DESC.
    # Optional ARG is the number of lines to output.

    local lines sql

    lines="${1:-10}"

    sql="\
  SELECT strftime('%Y-%m-%d', run_at) d, action, SUM(count) \
    FROM osiris \
GROUP BY d, action \
ORDER BY d DESC \
   LIMIT ${lines} \
;"

    sqlite3 -readonly statistics.db "${sql}"
}

main() {
    local arg1

    arg1="${1:-10}"
    if [[ "${arg1}" = "--all" ]]; then
        show_all
    else
        show "${arg1}"
    fi
}

main $@
