#!/bin/bash

# requrements
# - figlet
# - lolcat
# - bc

# /etc/update-motd.d

primary="\033[1;32m"  # Bright green
reset="\033[0m"  # Reset to default

convert_to_gi() {
    local number="$1"
    local unit="$2"
    local factor

    # Define conversion factors for each unit to Gi
    case "$unit" in
        Ki) factor="1048576" ;;   # 1 Gi = 2^20 Ki
        Mi) factor="1024" ;;      # 1 Gi = 2^10 Mi
        Gi) factor="1" ;;         # Already in Gi
        Ti) factor="0.000976563" ;; # 1 Ti = 2^-10 Gi
        Pi) factor="0.000000954" ;; # 1 Pi = 2^-20 Gi
        *) echo "Invalid unit: $unit" >&2; return 1 ;;
    esac

    # Perform the conversion using bc for precise arithmetic
    local result
    result=$(echo "scale=6; $number / $factor" | bc)

    # Print the result
    echo "$result Gi"
}

progress_bar() {
    local percentage=$1
    local bar_length=$2 # Length of the progress bar
    local filled_length=$((percentage * bar_length / 100))
    local empty_length=$((bar_length - filled_length))

    # ANSI escape codes for colors
    local dim_color="\033[2;37m"     # Dim gray

    # Create the progress bar
    local filled=$(printf "%0.s=" $(seq 1 $filled_length))
    local empty=$(printf "%0.s=" $(seq 1 $empty_length))

    # Display the bar with colors
    printf "[%b%s%b%s%b] %d%%\n" "$primary" "$filled" "$dim_color" "$empty" "$reset" "$percentage"
}

calculate_percentage() {
    local numerator=$1
    local denominator=$2

    # Check if the denominator is zero
    if (( $(echo "$denominator == 0" | bc -l) )); then
        echo 0
    fi

    # Calculate the percentage and round mathematically
    local result=$(echo "($numerator / $denominator) * 100" | bc -l)
    local percentage=$(echo "scale=0; ($result + 0.5) / 1" | bc)

    # Return the percentage
    echo "$percentage"
}

### HEADER
echo "MALIWAN" | figlet | /usr/games/lolcat -f

### Basic system info

UPTIME=$(uptime -p)
DISTRO=$(cat /etc/*release | grep '^PRETTY_NAME' | cut -d= -f2 | tr -d '"')
KERNEL=$(uname -s -r)
read LOAD1 LOAD5 LOAD15 <<<$(cat /proc/loadavg | awk '{ print $1,$2,$3 }')
# (1 min | 5 min | 15 min)

echo -e "
System info:
  Uptime....: $UPTIME
  Distro....: $DISTRO
  Kernel....: $KERNEL
  Load......: $primary$LOAD1$reset (1 min), $primary$LOAD5$reset (5 min), $primary$LOAD15$reset (15 min)
"

### Memory
# ram
read MEM_USED_VAL MEM_USED_UNIT MEM_TOTAL_VAL MEM_TOTAL_UNIT <<<$(free -htm | awk '/^Mem:/ {split($3, u, /[A-Za-z]+$/); split($2, t, /[A-Za-z]+$/); printf "%s %s %s %s", u[1], substr($3, length(u[1])+1), t[1], substr($2, length(t[1])+1)}')
# swap
read SWAP_USED_VAL SWAP_USED_UNIT SWAP_TOTAL_VAL SWAP_TOTAL_UNIT <<<$(free -htm | awk '/^Swap:/ {split($3, u, /[A-Za-z]+$/); split($2, t, /[A-Za-z]+$/); printf "%s %s %s %s", u[1], substr($3, length(u[1])+1), t[1], substr($2, length(t[1])+1)}')
echo -e "
Memory:
  $(printf "%-13s%13s" "RAM:" "$MEM_USED_VAL $MEM_USED_UNIT / $MEM_TOTAL_VAL $MEM_TOTAL_UNIT")    $(printf "%-13s%13s" "Swap:" "$SWAP_USED_VAL $SWAP_USED_UNIT / $SWAP_TOTAL_VAL $SWAP_TOTAL_UNIT")
  $(progress_bar $(calculate_percentage $MEM_USED_VAL $MEM_TOTAL_VAL) 20)    $(progress_bar $(calculate_percentage $SWAP_USED_VAL $SWAP_TOTAL_VAL) 20)
"

### Storage
read FILESYSTEM SIZE USED AVAILABLE USAGE MOUNT <<<$(df -h / | awk 'NR==2 {print $1, $2, $3, $4, $5, $6}')
echo -e "
Storage:
  $(printf "%-28s%28s" "$MOUNT" " $USED / $SIZE")
  $(progress_bar ${USAGE::-1} 50)
"

### kube ingress
echo -e "
Kubernetes Ingress:
$(kubectl get ingress -A -o jsonpath='{.items[*].spec.rules[*].host}' | tr ' ' '\n' | sort | uniq | sed 's/^/  /')
"

