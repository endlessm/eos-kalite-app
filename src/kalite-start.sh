#!/bin/bash
#
# kalite-start-sh
#
# Copyright (C) 2016 Endless Mobile, Inc.
# Authors:
#  Mario Sanchez Prada <mario@endlessm.com>
#  Niv Sardi <xaiki@endlessm.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

base_dir="/var/lib/kalite"
preloaded_dir="${base_dir}/PRELOADED"
content_dir="${base_dir}/content"

if [ ! -d ${base_dir} ]; then
    echo "No '${base_dir}' directory found"
    return
fi

if [ -d ${preloaded_dir} ]; then
    # Move pre-loaded content to its right place.
    mv ${preloaded_dir}/* ${base_dir}/ && rm -rf ${preloaded_dir}
    echo "Imported preloaded content"
fi

# Make sure there's always access to the assessment data
mkdir -p ${content_dir}
ln -snf /app/share/kalite/assessment ${content_dir}/assessment

# Use --foreground to prevent systemd establishing
# the connection via the socket too early
kalite start --foreground
