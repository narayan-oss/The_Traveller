from django.db import OperationalError
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from .models import Booking, Coach
from django.utils import timezone


@receiver(pre_save, sender=Booking)
def store_old_values(sender, instance, **kwargs):

    if instance.pk:                  # only for existing instances not new ones
        old_instance = Booking.objects.get(pk=instance.pk)
        cache.set(f'booking_old_{instance.pk}', {
            'old_booking_status' : old_instance.booking_status,
        }, 60)          # cache for 60 seconds


@receiver(post_save, sender=Booking)
def update_seats_count(sender, instance, created, **kwargs):

    if created:
        print("Booking instance created.")
        return

    old_data = cache.get(f'booking_old_{instance.pk}')

    if not old_data:
        return  # No cached data (edge case)
    
    old_status = old_data['old_booking_status']
    new_status = instance.booking_status

    # Only proceed if status actually changed
    if old_status == new_status:
        return

    try:
        coach = Coach.objects.get(
            train=instance.train,
            coach_type=instance.travel_class
        )
    except Coach.DoesNotExist:
        return  
    
    if old_status == 'Waiting' and new_status == 'Confirmed':
        coach.coach_seats = max(coach.coach_seats - 1, 0)  # Prevent negative seats
        print(f"Seats in {coach.coach_type} was reduced by 1 !")
        coach.save()

    
    elif old_status == 'Confirmed' and new_status == 'Cancelled':
        coach.coach_seats += 1
        print(f"Seats in {coach.coach_type} was increamented by 1 !")
        coach.save()
    
    else:
        print("instances with status waiting got deleted !")
        return




def daily_tasks():

    # 1. delete old bookings
    Booking.objects.filter(journey_date__lt=timezone.now().date()).delete()

    # 2. Reset coach seats
    today_weekday = timezone.now().weekday()
    coaches = Coach.objects.filter(day_of_reset__contains=str(today_weekday))

    for coach in coaches:
        coach.coach_seats = coach.total_seats
        coach.save()

def start_scheduler():

    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # will run daily at midnight
    scheduler.add_job(
        daily_tasks,
        trigger='cron',
        hour=0,
        minute=0,
        id="daily_maintainance",
        max_instances=1,
        replace_existing=True,
    )

    try:
        scheduler.start()
    except OperationalError:
        # Tables don't exist yet, we'll try again on next app ready
        pass
    except Exception as e:
        import logging
        logging.error(f"Failed to start scheduler: {e}")



# give users option to cancel their ticket
# delete booking older than current date
# reset the coach_seats back to full after journey completes