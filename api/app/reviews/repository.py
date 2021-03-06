from sqlalchemy.sql import func, exists
from sqlalchemy import and_
from app import db
from app.applicationModel.models import ApplicationForm
from app.responses.models import Response, ResponseReviewer
from app.reviews.models import ReviewForm, ReviewResponse, ReviewScore, ReviewQuestion
from app.users.models import AppUser
from app.events.models import EventRole

class ReviewRepository():

    @staticmethod
    def count_reviews_allocated_and_completed_per_reviewer(event_id):
        return db.engine.execute("""
                (
                    select 
                        email, 
                        user_title, 
                        firstname, 
                        lastname, 
                        0 as reviews_allocated, 
                        0 as reviews_completed
                    from app_user
                    join event_role on event_role.user_id = app_user.id
                    where event_role.role = 'reviewer'
                    and event_role.event_id = %d
                    and not exists (
                        select 1
                        from response_reviewer
                        where response_reviewer.reviewer_user_id = app_user.id
                    )
                )
                union
                (
                    select        
                        email, 
                        user_title, 
                        firstname, 
                        lastname, 
                        count(response_reviewer.id) as reviews_allocated, 
                        count(review_response.id) as reviews_completed
                    from response_reviewer
                    join app_user 
                    on response_reviewer.reviewer_user_id = app_user.id
                    join event_role 
                        on app_user.id = event_role.user_id 
                    join response 
                    on response.id = response_reviewer.response_id
                    left join review_response
                    on review_response.response_id = response.id
                    and review_response.reviewer_user_id = app_user.id
                    where 
                        event_role.role = 'reviewer'
                        and event_role.event_id = %d
                    group by app_user.id

                )
            """ % (event_id, event_id))

    @staticmethod
    def count_unassigned_reviews(event_id, required_reviews_per_response):
        responses =  (
            db.session.query(func.count(Response.id))
            .join(ApplicationForm, Response.application_form_id ==ApplicationForm.id)
            .filter(ApplicationForm.event_id == event_id)
            .filter(Response.is_submitted==True, Response.is_withdrawn==False)
            .first()[0]
        )

        reviews = (
            db.session.query(func.count(ResponseReviewer.id))
            .join(Response, ResponseReviewer.response_id ==Response.id)
            .join(ApplicationForm, Response.application_form_id ==ApplicationForm.id)
            .filter(ApplicationForm.event_id == event_id).first()[0]
        )

        return responses*required_reviews_per_response - reviews

    @staticmethod
    def get_review_form(event_id):
        review_form = (
            db.session.query(ReviewForm)
                    .join(ApplicationForm, ApplicationForm.id==ReviewForm.application_form_id)
                    .filter_by(event_id=event_id)
                    .first()
        )
        return review_form

    @staticmethod
    def get_remaining_reviews_count(reviewer_user_id, application_form_id):
        remaining = (
            db.session.query(func.count(ResponseReviewer.id))
                    .filter_by(reviewer_user_id=reviewer_user_id, active=True)
                    .join(Response)
                    .filter_by(is_withdrawn=False, application_form_id=application_form_id, is_submitted=True)
                    .outerjoin(ReviewResponse, and_(ReviewResponse.response_id==ResponseReviewer.response_id, ReviewResponse.reviewer_user_id==reviewer_user_id))
                    .filter_by(id=None)
                    .all()[0][0]
        )
        return remaining
    
    @staticmethod
    def get_response_to_review(skip, reviewer_user_id, application_form_id):
        response = (
            db.session.query(Response)
                    .filter_by(is_withdrawn=False, application_form_id=application_form_id, is_submitted=True)
                    .join(ResponseReviewer)
                    .filter_by(reviewer_user_id=reviewer_user_id, active=True)
                    .outerjoin(ReviewResponse, and_(ReviewResponse.response_id==ResponseReviewer.response_id, ReviewResponse.reviewer_user_id==reviewer_user_id))
                    .filter_by(id=None)
                    .order_by(ResponseReviewer.response_id)
                    .offset(skip)
                    .first()
        )
        return response

    @staticmethod
    def get_review_response_with_form(id, reviewer_user_id):
        review_form_response = (
            db.session.query(ReviewForm, ReviewResponse)
                    .join(ReviewResponse)
                    .filter_by(id=id, reviewer_user_id=reviewer_user_id)
                    .first()
        )
        return review_form_response

    @staticmethod
    def get_response_by_review_response(id, reviewer_user_id, application_form_id):
        response = (
            db.session.query(Response)
                    .filter_by(is_withdrawn=False, application_form_id=application_form_id, is_submitted=True)
                    .join(ResponseReviewer)
                    .filter_by(reviewer_user_id=reviewer_user_id)
                    .join(ReviewResponse)
                    .filter_by(id=id)
                    .first()
        )
        return response

    @staticmethod
    def get_response_reviewer(response_id, reviewer_user_id):
        response_reviewer = (
            db.session.query(ResponseReviewer)
                    .filter_by(response_id=response_id, reviewer_user_id=reviewer_user_id)
                    .first()
        )
        return response_reviewer

    @staticmethod
    def get_review_response(review_form_id, response_id, reviewer_user_id):
        review_response = (
            db.session.query(ReviewResponse)
                    .filter_by(review_form_id=review_form_id, response_id=response_id, reviewer_user_id=reviewer_user_id)
                    .first()
        )
        return review_response

    @staticmethod
    def add_model(model):
        db.session.add(model)
        db.session.commit()
        
    @staticmethod
    def get_review_history(reviewer_user_id, application_form_id):
        reviews = (db.session.query(ReviewResponse.id, ReviewResponse.submitted_timestamp, AppUser, ReviewScore.value, ReviewQuestion.options)
                        .filter(ReviewResponse.reviewer_user_id == reviewer_user_id)
                        .join(ReviewForm, ReviewForm.id == ReviewResponse.review_form_id)
                        .filter(ReviewForm.application_form_id == application_form_id)
                        .join(Response, ReviewResponse.response_id == Response.id)
                        .join(ReviewQuestion, ReviewForm.id == ReviewQuestion.review_form_id)
                        .filter(ReviewQuestion.headline == 'Final Verdict')
                        .join(ReviewScore, and_(ReviewQuestion.id == ReviewScore.review_question_id, ReviewResponse.id == ReviewScore.review_response_id))
                        .join(AppUser, Response.user_id == AppUser.id))
        return reviews

    @staticmethod
    def get_review_history_count(reviewer_user_id, application_form_id):
        count = (db.session.query(ReviewResponse)
                        .filter(ReviewResponse.reviewer_user_id == reviewer_user_id)
                        .join(ReviewForm, ReviewForm.id == ReviewResponse.review_form_id)
                        .filter(ReviewForm.application_form_id == application_form_id)
                        .count())
        return count