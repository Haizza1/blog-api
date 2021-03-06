"""Users views."""

# Rest framework
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework import status, viewsets, mixins

# Permissions
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated
)
from apps.users.permissions import IsAccountOwner

# Serializers
from apps.users.serializers import (
    UserModelSerializer,
    UserLoginSerializer,
    UserSignupSerializer,
    UserVerificationSerializer,
    ProfileModelSerializer
)

# Models 
from apps.users.models import User

class UsersViewSet(mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   viewsets.GenericViewSet):

    """Users view set"""

    queryset = User.objects.filter(is_active=True, is_client=True)
    lookup_field = 'username'
    look_url_kwarg = 'username'

    serializer_class = UserModelSerializer

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action in ['signup', 'login', 'verify']:
            permissions = [AllowAny]
        elif self.action in ['update', 'partial_update', 'profile']:
            permissions = [IsAuthenticated, IsAccountOwner]
        else:
            permissions = [IsAuthenticated]
        return [p() for p in permissions]


    @action(detail=False, methods=['POST'])
    def login(self, request):
        """Users sign in."""
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, token = serializer.save()
        data = {
            'user': UserModelSerializer(user).data,
            'token': token
        }

        return Response(data, status=status.HTTP_201_CREATED)
        

    @action(detail=False, methods=['POST'])
    def signup(self, request):
        """users sign up."""
        serializer = UserSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = UserModelSerializer(user).data

        return Response(data, status=status.HTTP_201_CREATED)


    @action(detail=False, methods=['POST'])
    def verify(self, request):
        """Account verification."""
        serializer = UserVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = {'message': 'Your account has been verified successfuly uwu'}

        return Response(data, status=status.HTTP_200_OK)


    @action(detail=True, methods=['put', 'patch'])
    def profile(self, request, *args, **kwargs):
        """Update profile data."""
        user = self.get_object()
        profile = user.profile
        partial = request.method == 'PATCH'
        serializer = ProfileModelSerializer(
            profile,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = UserModelSerializer(user).data
        return Response(data)


    @action(detail=True, methods=['POST'])
    def follow(self, request, *args, **kwargs):
        """Follow action."""
        user_from = request.user
        user_to = self.get_object()
        follows = False

        # Check if user_from already follows user_to

        if user_from.follow.filter(id=user_to.id).exists():
            user_from.follow.remove(user_to)
            follows = False
            user_to.profile.followers -= 1
            user_to.profile.save()

        else:
            user_from.follow.add(user_to)
            follows = True
            user_to.profile.followers += 1
            user_to.profile.save()

        if follows == True:
            message = 'Now you follow {}'.format(user_to.username)
        else:
            message = 'You unfollow {}'.format(user_to.username)

        data = {
            'user': UserModelSerializer(user_to).data,
            'message': message
        }

        return Response(data, status=status.HTTP_200_OK)