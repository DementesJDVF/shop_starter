from rest_framework import status


from apps.geo.models import Location
from apps.users.serializers import LocationSerializer
from django.shortcuts import get_list_or_404, get_object_or_404

@api_view(['GET', 'POST'])
def vendors_locations(request):
    
    if request.method == 'GET':
        locations = Location.objects.all()
        serializer = LocationSerializer(locations, many=True)
        return Response(serializer.data)
    
    if request.method ==  'POST':
        serializer = LocationSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['GET'])
def location_detail(request, id):
    location = get_object_or_404(Location, id=id)
    serializer = LocationSerializer(location)
    return Response(serializer.data)

2026-03-25 11:09:09.813 [info] > git check-ignore -v -z --stdin [61ms]2026-03-25 11:09:10.918 [info] > git check-ignore -v -z --stdin [57ms]2026-03-25 11:09:12.039 [info] > git check-ignore -v -z --stdin [75ms]2026-03-25 11:09:12.829 [info] > git config --get commit.template [65ms]2026-03-25 11:09:12.959 [info] > git status -z -uall [87ms]2026-03-25 11:09:13.142 [info] > git check-ignore -v -z --stdin [62ms]2026-03-25 11:09:12.989 [info] > git for-each-ref --sort -committerdate --format %(refname)%00%(objectname)%00%(*objectname) [93ms]2026-03-25 11:09:12.857 [info] > git for-each-ref --format=%(refname)%00%(upstream:short)%00%(objectname)%00%(upstream:track)%00%(upstream:remotename)%00%(upstream:remoteref) --ignore-case refs/heads/s4-location_vendor refs/remotes/s4-location_vendor [74ms]2026-03-25 11:09:13.357 [info] > git check-ignore -v -z --stdin [46ms]2026-03-25 11:09:14.430 [info] > git check-ignore -v -z --stdin [87ms]2026-03-25 11:09:15.489 [info] > git check-ignore -v -z --stdin [52ms]2026-03-25 11:09:16.535 [info] > git check-ignore -v -z --stdin [51ms]2026-03-25 11:09:17.565 [info] > git check-ignore -v -z --stdin [54ms]2026-03-25 11:09:18.165 [info] > git status -z -uall [56ms]2026-03-25 11:09:18.077 [info] > git config --get commit.template [58ms]2026-03-25 11:09:18.188 [info] > git for-each-ref --sort -committerdate --format %(refname)%00%(objectname)%00%(*objectname) [59ms]2026-03-25 11:09:18.097 [info] > git for-each-ref --format=%(refname)%00%(upstream:short)%00%(objectname)%00%(upstream:track)%00%(upstream:remotename)%00%(upstream:remoteref) --ignore-case refs/heads/s4-location_vendor refs/remotes/s4-location_vendor [62ms]2026-03-25 11:09:18.630 [info] > git check-ignore -v -z --stdin [50ms]2026-03-25 11:09:19.689 [info] > git check-ignore -v -z --stdin [52ms]2026-03-25 11:09:20.790 [info] > git check-ignore -v -z --stdin [52ms]2026-03-25 11:09:21.872 [info] > git check-ignore -v -z --stdin [54ms]2026-03-25 11:09:22.924 [info] > git check-ignore -v -z --stdin [51ms]2026-03-25 11:09:23.264 [info] > git config --get commit.template [54ms]2026-03-25 11:09:23.411 [info] > git status -z -uall [96ms]2026-03-25 11:09:23.433 [info] > git for-each-ref --sort -committerdate --format %(refname)%00%(objectname)%00%(*objectname) [101ms]2026-03-25 11:09:23.300 [info] > git for-each-ref --format=%(refname)%00%(upstream:short)%00%(objectname)%00%(upstream:track)%00%(upstream:remotename)%00%(upstream:remoteref) --ignore-case refs/heads/s4-location_vendor refs/remotes/s4-location_vendor [76ms]2026-03-25 11:09:23.799 [info] > git check-ignore -v -z --stdin [52ms]2026-03-25 11:09:24.054 [info] > git check-ignore -v -z --stdin [57ms]2026-03-25 11:09:24.915 [info] > git check-ignore -v -z --stdin [63ms]2026-03-25 11:09:25.183 [info] > git check-ignore -v -z --stdin [59ms]2026-03-25 11:09:26.207 [info] > git check-ignore -v -z --stdin [57ms]2026-03-25 11:09:27.348 [info] > git check-ignore -v -z --stdin [96ms]2026-03-25 11:09:27.813 [info] > git -c user.useConfigOnly=true commit --quiet --allow-empty-message --file - [70ms]2026-03-25 11:09:27.893 [info] > git config --get-all user.name [64ms]2026-03-25 11:09:27.970 [info] > git config --get commit.template [65ms]2026-03-25 11:09:28.060 [info] > git status -z -uall [62ms]2026-03-25 11:09:28.080 [info] > git for-each-ref --sort -committerdate --format %(refname)%00%(objectname)%00%(*objectname) [67ms]2026-03-25 11:09:27.987 [info] > git for-each-ref --format=%(refname)%00%(upstream:short)%00%(objectname)%00%(upstream:track)%00%(upstream:remotename)%00%(upstream:remoteref) --ignore-case refs/heads/s4-location_vendor refs/remotes/s4-location_vendor [67ms]2026-03-25 11:09:28.539 [info] > git check-ignore -v -z --stdin [45ms]2026-03-25 11:09:29.377 [info] > git check-ignore -v -z --stdin [54ms]2026-03-25 11:09:29.639 [info] > git check-ignore -v -z --stdin [51ms]2026-03-25 11:09:30.497 [info] > git check-ignore -v -z --stdin [57ms]2026-03-25 11:09:30.741 [info] > git check-ignore -v -z --stdin [48ms]2026-03-25 11:09:31.592 [info] > git check-ignore -v -z --stdin [60ms]2026-03-25 11:09:31.833 [info] > git check-ignore -v -z --stdin [49ms]2026-03-25 11:09:33.388 [info] > git check-ignore -v -z --stdin [58ms]2026-03-25 11:09:34.674 [info] > git check-ignore -v -z --stdin [55ms]2026-03-25 11:09:36.154 [info] > git check-ignore -v -z --stdin [54ms]2026-03-25 11:09:37.245 [info] > git check-ignore -v -z --stdin [52ms]2026-03-25 11:09:38.388 [info] > git check-ignore -v -z --stdin [54ms]2026-03-25 11:09:39.471 [info] > git check-ignore -v -z --stdin [53ms]2026-03-25 11:09:40.519 [info] > git check-ignore -v -z --stdin [53ms]