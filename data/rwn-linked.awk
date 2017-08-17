#!/usr/bin/awk -f
BEGIN {
    FS = OFS = "\t";
}
{
    gsub(/ /, "_", $3);
    gsub(/ /, "_", $5);

    gsub(/\|/, ", ", $3);
    gsub(/\|/, ", ", $5);

    print $1, $2, tolower($3), $4, tolower($5);
}
