#!/bin/bash


for ip in `seq 1 254`; do 
ping -c 1 $1.$ip | grep "64 bytes" | cut -d " " -f 4 | tr -d ":" &
done

./sweeper.sh 10.0.2.15
