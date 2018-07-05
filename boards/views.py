from django.shortcuts import render
from .models import User
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, View
from .models import Board, BoardMember, Referral, Column
from .forms import BoardModalForm, MembersModalForm, UserValidationForm
from annoying.functions import get_object_or_None
from django.http import HttpResponse, HttpResponseRedirect,HttpResponseBadRequest
from django.shortcuts import reverse
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from users.mixins import ThrowHomeIfLoggedInMixIn
from django.contrib.auth import logout, authenticate, login
from django.http import JsonResponse
from django.core import serializers


class IndexView(LoginRequiredMixin,TemplateView):
    """
        Views for the Index Page
    """
    # Reverse lazy is needed since this code is before the Url coniguration
    # is loaded
    login_url = reverse_lazy('users:log_in')
    template_name = "boards/index.html"
    form = BoardModalForm

    def get(self, *args,** kwargs):
        context = self.form()
        username = self.kwargs.get('username')
        user = get_object_or_404(User,username=username)
        boards = BoardMember.objects.filter(
            user=user,board__archived=False,is_confirmed=True)
        return render(self.request, self.template_name,
            {'form':context, 'boards': boards, 'current_user' : username}
        )

    
    def post(self, *args,** kwargs):
        form = self.form(self.request.POST)
        username = self.request.user.get_username()
        user = get_object_or_404(User,username=username)
        if form.is_valid():
            form.save_board(user)
            boards = BoardMember.objects.filter(
                user=user,board__archived=False,is_confirmed=True)
            form = self.form()
            return render(self.request, self.template_name,
                {'form':form, 'boards': boards, 'current_user' : username}
            )
        else:
             boards = BoardMember.objects.filter(
                user=user,board__archived=False,is_confirmed=True)
        
        return render(self.request, self.template_name, 
            {'form':form, 'boards': boards, 'current_user' : username}
        )


class BoardView(LoginRequiredMixin, TemplateView):
    # Reverse lazy is needed since this code is before the Url coniguration
    # is loaded
    login_url = reverse_lazy('users:log_in')
    template_name = "boards/boards.html"
    board_form = BoardModalForm
    member_form = MembersModalForm


    def get(self, *args,** kwargs):
        board_form = self.board_form()
        member_form = self.member_form()
        board_id = self.kwargs.get('id')
        username = self.request.user.get_username()
        access = get_object_or_404(BoardMember,user__username=username,
            is_confirmed=True,board__id=board_id)
        board = get_object_or_404(Board,pk=board_id)
        board_member = BoardMember.objects.filter(
            board__id=board_id).exclude(user=board.owner)
        columns = Column.objects.filter(
            board__id=board_id,archived=False).order_by('position')
        owner = False
        if board.owner == self.request.user:
            owner = True
        return render(self.request, self.template_name,
            {
                'board_form': board_form, 'member_form': member_form,
                'board':board, 'current_user' : username, 'message_box': None,
                'owner' : owner, 'board_member' : board_member, 'columns' : columns
            }
        )


    def post(self, *args,** kwargs):
        board_id = self.kwargs.get('id')
        username = self.request.user.get_username()
        access = get_object_or_404(BoardMember,user__username=username,
            is_confirmed=True,board__id=board_id)
        board = get_object_or_404(Board,pk=board_id)
        columns = Column.objects.filter(
            board__id=board_id,archived=False).order_by('position')
        owner = False
        board_member = BoardMember.objects.filter(
            board__id=board_id).exclude(user=board.owner)
        if board.owner == self.request.user:
            owner = True
        # Edit Board Form
        if 'EditModal' in self.request.POST:
            member_form = self.member_form()
            board_form = self.board_form(self.request.POST)
            if owner == True:
                if board_form.is_valid():
                    board = board_form.update_board(board)
                    board_form = self.board_form()
                    return render(self.request, self.template_name,
                        {
                            'board_form': board_form, 'member_form': member_form,
                            'board':board, 'current_user' : username,
                            'message_box':None, 'owner' : owner, 'board_member' : board_member
                        }
                    )
            # Failing validation will render this template below
            return render(self.request, self.template_name,
                {
                 'board_form': board_form, 'member_form': member_form,
                 'board':board, 'current_user' : username,
                 'message_box':None, 'owner' : owner, 'board_member' : board_member
                }
            )
        # Archiving Board Form
        elif 'ArchiveBoardModal' in self.request.POST:
            board_form = self.board_form()
            member_form = self.member_form()
            if owner == True:
                board = board_form.archive_board(board)
                return HttpResponseRedirect(reverse('boards:home' , 
                    kwargs={'username': username 
                }))
            # Failing validation will render template below
            return render(self.request, self.template_name,
                {
                    'board_form': board_form, 'member_form': member_form,
                    'board':board, 'current_user' : username,
                    'message_box': None, 'owner' : owner, 'board_member' : board_member
                }
            )
        # Inviting a member form
        elif 'AddMemberModal' in self.request.POST:
            member_form = self.member_form(self.request.POST , board_id=board_id)
            board_form = self.board_form()

            if member_form.is_valid():
                host = self.request.get_host()
                member_form.invite(host, username, board)
                # This function creates an object define the values of the message box modal
                # Currently limited on one button since I don't need multiple buttons
                message_box = {
                        'title' : 'Success', 'message': 'The user is successfully invited',
                        'button' : 'OK'
                    }
                return render(self.request, self.template_name,
                    {
                       'board_form': board_form, 'member_form': member_form,
                       'board':board, 'current_user' : username,
                        'message_box':message_box, 'owner' : owner, 'board_member' : board_member
                    }
                )

            # Falls here if the validation failed
            return render(self.request, self.template_name,
                {
                   'board_form': board_form, 'member_form': member_form,
                   'board':board, 'current_user' : username,
                   'message_box':None, 'owner' : owner, 'board_member' : board_member
                }
            )
        elif 'RemoveMemberModal' in self.request.POST:
            stacked_id_to_remove = self.request.POST.getlist('remove_member')
            member_form = self.member_form()
            board_form = self.board_form()
            member_form.remove_member(stacked_id_to_remove)
            return render(self.request, self.template_name,
                {
                   'board_form': board_form, 'member_form': member_form,
                   'board':board, 'current_user' : username,
                   'message_box':None, 'owner' : owner, 'board_member' : board_member
                }
            )

class AddColumnView(View):
    """
    """

    def post(self, *args, **kwargs):
        title = self.request.POST.get('title')
        board_id = self.kwargs.get('id')
        board = get_object_or_404(Board,pk=board_id)
        new_column = Column(board=board,name=title,position=0)
        new_column.save()
        all_columns = Column.objects.filter(board__id=board_id)
        data=serializers.serialize('json', all_columns)
        return HttpResponse(data)
        


class UserValidationView(TemplateView):
    """
        Views for the User Validation Page
    """
    template_name = "boards/user_validation.html"
    form = UserValidationForm

    def get(self, *args, **kwargs):
        token = self.kwargs.get('token')
        referral = get_object_or_404(Referral, token=token)
        board = referral.board_member.board
        email = referral.email
        form = self.form()
        if referral:
            # Checking if the user exists
            user = get_object_or_None(User, email=referral.email)
            if user:
                proceed = False
                # Check if the user is already logged in
                if not self.request.user.is_authenticated:
                    user = form.login(self.request, user=user)
                    proceed = True
                else:
                    if self.request.user.email == email:
                        user = self.request.user
                        proceed = True
                       
                if proceed:
                    # falls short when the logged in user is not the same referral email
                    return render(self.request, self.template_name,
                        {'form':form, 'email' : email, 'board': board , 'account' : True}
                    )
            else:
                return render(self.request, self.template_name,
                    {'form':form, 'email' : email, 'board': board, 'account' : False}
                ) 
        return HttpResponseBadRequest()

    def post(self, *args, **kwargs):
        form = self.form(self.request.POST)
        user = self.request.user
        token = self.kwargs.get('token')
        referral = get_object_or_404(Referral, token=token)
        board = referral.board_member.board
        email = referral.email
        if 'JoinBoard' in self.request.POST:
            # User Is Already Registered

            board_id = form.join_board(user, token)
            return HttpResponseRedirect(reverse('boards:board' , kwargs={'id':board_id  }))
        elif 'ReferralSignUp' in self.request.POST:
            if form.is_valid():
                user = form.save(email)
                user = form.login(self.request, user=user)
                board_id = form.join_board(user,token)
                return HttpResponseRedirect(reverse('boards:board' , kwargs={'id':board_id  }))
            else:
                return render(self.request, self.template_name,
                    {'form':form, 'email' : email, 'board': board , 'success': True , 'account' : False}
                ) 
        return HttpResponseBadRequest()

