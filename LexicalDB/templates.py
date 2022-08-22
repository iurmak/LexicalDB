from LexicalDB import app
from flask import render_template, request, url_for, session, make_response, jsonify, redirect
from LexicalDB.supplement import Emails, Amend, Check
from LexicalDB.models import db, Users, Taxonomy, Topology, Semantic_roles, Participants, Participant_relations,\
    Event_structure, Templates, Template_relations,\
    Examples, Event_structure_relations
from itsdangerous import URLSafeSerializer
from re import sub, compile


@app.route('/edit/template/<int:templ_id>', methods=['POST', 'GET'])
def edit_template(templ_id):
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id not in [2, 3]:
        return Check.status()
    if request.method == 'GET':
        return render_template("edit_template.html",
                               templ_id=templ_id,
                               Taxonomy=Taxonomy,
                               Templates=Templates,
                               Template_relations=Template_relations,
                               Topology=Topology,
                               Semantic_roles=Semantic_roles,
                               Participants=Participants,
                               Participant_relations=Participant_relations,
                               Examples=Examples,
                               Event_structure=Event_structure,
                               Event_structure_relations=Event_structure_relations,
                               Amend=Amend,
                               Check=Check
                               )

    elif request.method == 'POST':
        no_spaces_at_edges = compile(r'( +$|^ +)')
        Templates.query.filter_by(templ_id=templ_id).update(
            {'templ': request.form.get('template_name')}
        )
        Template_relations.query.filter_by(target_id=templ_id, type=1).delete()
        if request.form.to_dict(flat=False).get('based_on'):
            for base in request.form.to_dict(flat=False).get('based_on'):
                db.session.add(
                    Template_relations(
                        templ_id=base,
                        target_id=templ_id,
                        type=1
                    )
                )

        all_semantic_roles = [no_spaces_at_edges.sub('', request.form.get(i)) for i in request.form if
                              i.startswith('sr_') and request.form.get(i)]
        for sr in all_semantic_roles:
            if not Semantic_roles.query.filter_by(sr=sr).first():
                db.session.add(
                    Semantic_roles(
                        sr=sr
                    )
                )
                db.session.commit()

        all_new_taxonomy = [request.form.get(i) for i in request.form if
                            i.startswith('new_tax_') and no_spaces_at_edges.sub('', request.form.get(i))]
        for new_tax in all_new_taxonomy:
            for tax in new_tax.split(','):
                if not Taxonomy.query.filter_by(tax=tax).first() and no_spaces_at_edges.sub('', tax):
                    db.session.add(
                        Taxonomy(
                            tax=no_spaces_at_edges.sub('', tax)
                        )
                    )
                    db.session.commit()

        all_new_topology = [request.form.get(i) for i in request.form if
                            i.startswith('new_top_') and no_spaces_at_edges.sub('', request.form.get(i))]
        for new_top in all_new_topology:
            for top in new_top.split(','):
                if not Topology.query.filter_by(top=top).first() and no_spaces_at_edges.sub('', top):
                    db.session.add(
                        Topology(
                            top=no_spaces_at_edges.sub('', top)
                        )
                    )
                    db.session.commit()

        participants_to_delete = [request.form.get(i) for i in request.form if i.startswith('delete_p_') and request.form.get(i)]
        for p in participants_to_delete:
            Template_relations.query.filter_by(templ_id=templ_id, target_id=p, type=9).delete()

        all_participants = [i.split('_')[-1] for i in request.form if i.startswith('label_') and request.form.get(i)]
        for p in all_participants:
            if no_spaces_at_edges.sub('', request.form.get(f'sr_{p}')):
                sr_id = Semantic_roles.query.filter_by(
                    sr=no_spaces_at_edges.sub('', request.form.get(f'sr_{p}'))).first().sr_id
            else:
                sr_id = ''

            participant = Participants(
                participant=no_spaces_at_edges.sub('', request.form.get(f'label_{p}')),
                sr_id=sr_id,
                other=no_spaces_at_edges.sub('', request.form.get(f'other_{p}')),
                status=request.form.get(f'status_{p}')
            )
            db.session.add(participant)
            db.session.commit()
            db.session.add(
                Template_relations(
                    templ_id=templ_id,
                    target_id=participant.participant_id,
                    type=9
                )
            )
            if request.form.to_dict(flat=False).get(f'is_child_{p}'):
                for base in request.form.to_dict(flat=False).get(f'is_child_{p}'):
                    db.session.add(
                        Participant_relations(
                            participant_id=base,
                            target_id=participant.participant_id,
                            type=3
                        )
                    )
                db.session.commit()
            for tax in [i for i in request.form if i.startswith(f'tax_{p}_') and request.form.get(i)]:
                db.session.add(
                    Participant_relations(
                        participant_id=participant.participant_id,
                        target_id=int(tax.split('_')[-1]),
                        type=1
                    )
                )
                db.session.commit()
            for tax in request.form.get(f'new_tax_{p}').split(','):
                if no_spaces_at_edges.sub('', tax):
                    db.session.add(
                        Participant_relations(
                            participant_id=participant.participant_id,
                            target_id=Taxonomy.query.filter_by(tax=no_spaces_at_edges.sub('', tax)).first().tax_id,
                            type=1
                        )
                    )
                    db.session.commit()

            for top in [i for i in request.form if i.startswith(f'top_{p}_') and request.form.get(i)]:
                db.session.add(
                    Participant_relations(
                        participant_id=participant.participant_id,
                        target_id=int(top.split('_')[-1]),
                        type=2
                    )
                )
                db.session.commit()
            for top in request.form.get(f'new_top_{p}').split(','):
                if no_spaces_at_edges.sub('', top):
                    db.session.add(
                        Participant_relations(
                            participant_id=participant.participant_id,
                            target_id=Topology.query.filter_by(top=no_spaces_at_edges.sub('', top)).first().top_id,
                            type=2
                        )
                    )
                    db.session.commit()
        Examples.query.filter_by(example_id=Template_relations.query.filter_by(templ_id=templ_id, type=3).first().target_id).update({'example': request.form.get('example')})
        db.session.commit()

        ese_to_delete = [request.form.get(i) for i in request.form if
                         i.startswith('delete_ese_') and request.form.get(i)]
        for ese in ese_to_delete:
            Template_relations.query.filter_by(templ_id=templ_id, target_id=ese, type=2).delete()
            Event_structure.query.filter_by(ese_id=ese).delete()
            Event_structure_relations.query.filter_by(element_id=ese).delete()
            db.session.commit()

        event_structure = [(1, 'I'), (2, 'B'),
                           (3, 'P'), (4, 'F'),
                           (5, 'R'), (6, 'Impl')]
        for event_structure_part in event_structure:
            for i in [part for part in request.form if
                      part.startswith(f'{event_structure_part[-1]}_') and request.form.get(part)]:
                item = Event_structure(ese=no_spaces_at_edges.sub('', request.form.get(i)),
                                       rank=request.form.get(f'rank_{event_structure_part[-1]}_{i.split("_")[-1]}'),
                                       type=event_structure_part[0]
                                       )
                db.session.add(item)
                db.session.commit()
                if request.form.get(f'is_child_{event_structure_part[-1]}_{i.split("_")[-1]}'):
                    db.session.add(
                        Event_structure_relations(
                            element_id=item.ese_id,
                            target_id=request.form.get(f'is_child_{event_structure_part[-1]}_{i.split("_")[-1]}'),
                            type=1
                        )
                    )
                db.session.add(
                    Template_relations(
                        templ_id=templ_id,
                        target_id=item.ese_id,
                        type=2
                    )
                )
                db.session.commit()
            for i in [part for part in request.form if
                      part.startswith(f'existent_{event_structure_part[-1]}_')]:
                i_id = int(i.split('_')[-1])
                Event_structure.query.filter_by(ese_id=i_id, type=event_structure_part[0]).update(
                    {'ese': no_spaces_at_edges.sub('', request.form.get(i)),
                     'rank': request.form.get(f'rank_existent_{event_structure_part[-1]}_{i.split("_")[-1]}')}
                )
                db.session.commit()
                Event_structure_relations.query.filter_by(element_id=i_id, type=1).delete()
                if request.form.get(f'is_child_existent_{event_structure_part[-1]}_{i.split("_")[-1]}'):
                    db.session.add(
                        Event_structure_relations(
                            element_id=i_id,
                            target_id=request.form.get(f'is_child_existent_{event_structure_part[-1]}_{i.split("_")[-1]}'),
                            type=1
                        )
                    )
                db.session.commit()
        return redirect(url_for('edit_template', templ_id=templ_id))

@app.route('/edit/new_template', methods=['POST', 'GET'])
def new_template():
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id not in [2, 3]:
        return Check.status()

    if request.method == 'GET':
        return render_template("new_template.html",
                               Taxonomy=Taxonomy,
                               Templates=Templates,
                               Topology=Topology,
                               Semantic_roles=Semantic_roles,
                               Participants=Participants,
                               Event_structure=Event_structure
                               )

    elif request.method == 'POST':
        no_spaces_at_edges = compile(r'( +$|^ +)')
        template = Templates(
            templ=request.form.get('template_name'),
            created_by=user_id,
            datetime=Check.time()
        )
        db.session.add(template)
        db.session.commit()
        if request.form.to_dict(flat=False).get('based_on'):
            for base in request.form.to_dict(flat=False).get('based_on'):
                db.session.add(
                    Template_relations(
                        templ_id=base,
                        target_id=template.templ_id,
                        type=1
                    )
                )

        all_semantic_roles = [no_spaces_at_edges.sub('', request.form.get(i)) for i in request.form if
                              i.startswith('sr_') and request.form.get(i)]
        for sr in all_semantic_roles:
            if not Semantic_roles.query.filter_by(sr=sr).first():
                db.session.add(
                    Semantic_roles(
                        sr=sr
                    )
                )
                db.session.commit()

        all_new_taxonomy = [request.form.get(i) for i in request.form if
                            i.startswith('new_tax_') and no_spaces_at_edges.sub('', request.form.get(i))]
        for new_tax in all_new_taxonomy:
            for tax in new_tax.split(','):
                if not Taxonomy.query.filter_by(tax=tax).first() and no_spaces_at_edges.sub('', tax):
                    db.session.add(
                        Taxonomy(
                            tax=no_spaces_at_edges.sub('', tax)
                        )
                    )
                    db.session.commit()

        all_new_topology = [request.form.get(i) for i in request.form if
                            i.startswith('new_top_') and no_spaces_at_edges.sub('', request.form.get(i))]
        for new_top in all_new_topology:
            for top in new_top.split(','):
                if not Topology.query.filter_by(top=top).first() and no_spaces_at_edges.sub('', top):
                    db.session.add(
                        Topology(
                            top=no_spaces_at_edges.sub('', top)
                        )
                    )
                    db.session.commit()

        all_participants = [i.split('_')[-1] for i in request.form if i.startswith('label_') and request.form.get(i)]
        for p in all_participants:
            if no_spaces_at_edges.sub('', request.form.get(f'sr_{p}')):
                sr_id = Semantic_roles.query.filter_by(sr=no_spaces_at_edges.sub('', request.form.get(f'sr_{p}'))).first().sr_id
            else:
                sr_id = ''

            participant = Participants(
                participant=no_spaces_at_edges.sub('', request.form.get(f'label_{p}')),
                sr_id=sr_id,
                other=no_spaces_at_edges.sub('', request.form.get(f'other_{p}')),
                status=request.form.get(f'status_{p}')
            )
            db.session.add(participant)
            db.session.commit()
            db.session.add(
                Template_relations(
                    templ_id=template.templ_id,
                    target_id=participant.participant_id,
                    type=9
                )
            )
            if request.form.to_dict(flat=False).get(f'is_child_{p}'):
                for base in request.form.to_dict(flat=False).get(f'is_child_{p}'):
                    db.session.add(
                        Participant_relations(
                            participant_id=base,
                            target_id=participant.participant_id,
                            type=3
                        )
                    )
                db.session.commit()
            for tax in [i for i in request.form if i.startswith(f'tax_{p}_') and request.form.get(i)]:
                db.session.add(
                    Participant_relations(
                        participant_id=participant.participant_id,
                        target_id=int(tax.split('_')[-1]),
                        type=1
                    )
                )
                db.session.commit()
            for tax in request.form.get(f'new_tax_{p}').split(','):
                if no_spaces_at_edges.sub('', tax):
                    db.session.add(
                        Participant_relations(
                            participant_id=participant.participant_id,
                            target_id=Taxonomy.query.filter_by(tax=no_spaces_at_edges.sub('', tax)).first().tax_id,
                            type=1
                        )
                    )
                    db.session.commit()

            for top in [i for i in request.form if i.startswith(f'top_{p}_') and request.form.get(i)]:
                db.session.add(
                    Participant_relations(
                        participant_id=participant.participant_id,
                        target_id=int(top.split('_')[-1]),
                        type=2
                    )
                )
                db.session.commit()
            for top in request.form.get(f'new_top_{p}').split(','):
                if no_spaces_at_edges.sub('', top):
                    db.session.add(
                        Participant_relations(
                            participant_id=participant.participant_id,
                            target_id=Topology.query.filter_by(top=no_spaces_at_edges.sub('', top)).first().top_id,
                            type=2
                        )
                    )
                    db.session.commit()
        example = Examples(
                example=request.form.get('example')
            )
        db.session.add(example)
        db.session.commit()
        db.session.add(
            Template_relations(
                templ_id=template.templ_id,
                target_id=example.example_id,
                type=3
            )
        )
        db.session.commit()

        event_structure = [(1, 'I'), (2, 'B'),
                           (3, 'P'), (4, 'F'),
                           (5, 'R'), (6, 'Impl')]
        for event_structure_part in event_structure:
            for i in [part for part in request.form if
                      part.startswith(f'{event_structure_part[-1]}_') and request.form.get(part)]:
                item = Event_structure(ese=no_spaces_at_edges.sub('', request.form.get(i)),
                                       rank=request.form.get(f'rank_{event_structure_part[-1]}_{i.split("_")[-1]}'),
                                       type=event_structure_part[0]
                                       )
                db.session.add(item)
                db.session.commit()
                if request.form.get(f'is_child_{event_structure_part[-1]}_{i.split("_")[-1]}'):
                    db.session.add(
                        Event_structure_relations(
                            element_id=item.ese_id,
                            target_id=request.form.get(f'is_child_{event_structure_part[-1]}_{i.split("_")[-1]}'),
                            type=1
                        )
                    )
                db.session.add(
                    Template_relations(
                        templ_id=template.templ_id,
                        target_id=item.ese_id,
                        type=2
                    )
                )
                db.session.commit()
        return redirect(url_for('edit_template', templ_id=template.templ_id))

@app.route('/templates', methods=['POST', 'GET'])
@app.route('/templates/<int:page>', methods=['POST', 'GET'])
def templates(page=1):
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id not in [2, 3]:
        return Check.status()

    if request.method == 'GET':
        page_of_templates = Templates.query.order_by(Templates.templ_id.desc()).paginate(page, 20)
        templates = page_of_templates.items
        return render_template("templates.html",
                               Templates=Templates,
                               Template_relations=Template_relations,
                               templates=templates,
                               items=page_of_templates,
                               Participants=Participants,
                               Amend=Amend
                               )
    elif request.method == 'POST':
        if request.form.get('query'):
            if (request.form.get('parameter') == 'ID'):
                try:
                    templates = Templates.query.filter_by(templ_id=int(request.form.get('query'))).order_by(Templates.templ_id.desc()).all()
                    page_of_templates = None
                except:
                    return Amend.flash('Введите число.', 'danger', url_for('templates'))
            return render_template('templates.html',
                                   Templates=Templates,
                                   Template_relations=Template_relations,
                                   templates=templates,
                                   items=page_of_templates,
                                   Participants=Participants,
                                   Amend=Amend
                                   )
        return Amend.flash('Введите поисковый запрос.', 'danger', url_for('templates'))

@app.route('/edit/autocomplete', methods=['POST'])
def editing_autocomplete():
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id not in [2, 3]:
        return Check.status()
    if request.method == 'POST':
        no_spaces_at_edges = compile(r'( +$|^ +)')
        type, input = (request.get_json().get('type'), request.get_json().get('input'))
        if len(input) < 3 and type not in ['existent_participant', 'p_label_availability']:
            return None
        if type == 'I':
            response = jsonify([i.ese for i in Event_structure.query.filter_by(type=1).filter(Event_structure.ese.contains(input)).limit(5).all()])
        elif type == 'B':
            response = jsonify([i.ese for i in Event_structure.query.filter_by(type=2).filter(Event_structure.ese.contains(input)).limit(5).all()])
        elif type == 'P':
            response = jsonify([i.ese for i in Event_structure.query.filter_by(type=3).filter(Event_structure.ese.contains(input)).limit(5).all()])
        elif type == 'F':
            response = jsonify([i.ese for i in Event_structure.query.filter_by(type=4).filter(Event_structure.ese.contains(input)).limit(5).all()])
        elif type == 'R':
            response = jsonify([i.ese for i in Event_structure.query.filter_by(type=5).filter(Event_structure.ese.contains(input)).limit(5).all()])
        elif type == 'Impl':
            response = jsonify([i.ese for i in Event_structure.query.filter_by(type=6).filter(Event_structure.ese.contains(input)).limit(5).all()])
        elif type == 'sr':
            response = jsonify([i.sr for i in Semantic_roles.query.filter(Semantic_roles.sr.contains(input)).limit(5).all()])
        elif type == 'p_label_availability':
            if Participants.query.filter_by(participant=no_spaces_at_edges.sub('', input)).first():
                response = jsonify(0)
            else:
                response = jsonify(1)
        elif type == 'template_availability':
            if Templates.query.filter_by(templ=no_spaces_at_edges.sub('', input)).first() and request.get_json().get('templ_id') != Templates.query.filter_by(templ=no_spaces_at_edges.sub('', input)).first().templ_id:
                response = jsonify(0)
            else:
                response = jsonify(1)
        elif type == 'existent_participant':
            taxonomy_ids = [i.target_id for i in Participant_relations.query.filter_by(participant_id=input, type=1).all()]
            topology_ids = [i.target_id for i in
                            Participant_relations.query.filter_by(participant_id=input, type=2).all()]
            if Participants.query.get(input).sr_id:
                sr = Semantic_roles.query.get(Participants.query.get(input).sr_id).sr
            else:
                sr = ''
            if Participants.query.get(input).other:
                other = Participants.query.get(input).other
            else:
                other = ''
            response = jsonify({
                'label': Participants.query.get(input).participant,
                'sr': sr,
                'tax': taxonomy_ids,
                'top': topology_ids,
                'other': other,
                'status': Participants.query.get(input).status,
                'parents': [p.participant_id for p in Participant_relations.query.filter_by(target_id=input, type=3).all()]
            })
        return make_response(response, 200)
