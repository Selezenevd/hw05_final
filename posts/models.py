from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(verbose_name="URL", max_length=50, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="posts",
    )
    group = models.ForeignKey(
        Group, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name="posts",
    )
    
    # поле для картинки
    image = models.ImageField(upload_to='posts/', blank=True, null=True)  

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        # return (f'{self.group.title}, '
        #         f'{self.author.username}, '
        #         f'{self.pub_date.strftime}, '
        #         f'{self.text[:100]}')
        return self.text

class Comment(models.Model):
    post = models.ForeignKey(
        Post,  
        on_delete=models.CASCADE,  
        related_name='comments'
    ) 
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="comments",
    )
    text = models.TextField() 
    created = models.DateTimeField("date published", auto_now_add=True)

    class Meta:  
        ordering = ('created',) 

    def __str__(self):  
        return 'Comment by {} on {}'.format(self.author, self.post)


class Follow(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="follower",
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="following",
    )
    
    class Meta:
        models.UniqueConstraint(
            fields=['user', 'author'], 
            name='following_unique',
        )
