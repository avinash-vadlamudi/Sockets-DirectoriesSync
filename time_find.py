string = raw_input("Enter Date mon yr hr min sec : ")
values = string.split(" ")
ans = 0
date = int(values[0])
mon = int(values[1])
yr = int(values[2])

hr = int(values[3])
mins = int(values[4])
sec = int(values[5])

for i in range(1970,yr):
    if i%4 == 0:
        if i%100 == 0 and i%400 == 0:
            ans = ans+86400*366
        elif i%100 == 0:
            ans = ans+86400*365
        else:
            ans = ans+86400*366
    else:
        ans = ans + 86400*365

for i in range(1,mon):
    if i == 1 or i==3 or i==5 or i==7 or i==8 or i==10 or i==12:
        ans = ans + 86400*31
    elif i==2:
        if yr%4==0:
            if yr%100 == 0 and yr%400 == 0:
                ans = ans+86400*29
            else:
                ans = ans + 86400*28
        else:
            ans = ans+86400*28
    else:
        ans = ans + 86400*30

ans = ans+86400*(date-1)
ans = ans + 3600*(hr)
ans = ans + 60*mins
ans = ans + sec
ans = ans - 5*3600 - 30*60
print ans
