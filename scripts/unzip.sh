#!/bin/bash

for zipfile in *.zip; do
  dir="${zipfile%.zip}"
  mkdir -p "$dir"
  unzip -d "$dir" "$zipfile" && rm -f "$zipfile"
done

