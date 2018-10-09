#!bin/bash


show() {
    # Print actions counts day by day DESC.
    # Oprional ARG is the number of lines to output.

    local ndays sql

    [ -z "$1" ] && lines="10" || lines="$1"

    sql="\
  SELECT strftime('%Y-%m-%d', run_at) d, action, SUM(count) \
    FROM osiris \
GROUP BY d, action \
ORDER BY d DESC \
   LIMIT ${lines} \
;"

    sqlite3 statistics.db "${sql}"
}

show $@
