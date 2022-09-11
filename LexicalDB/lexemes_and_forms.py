from LexicalDB import app
from flask import render_template, request, url_for, session, make_response, jsonify, redirect
from LexicalDB.supplement import Emails, Amend, Check
from LexicalDB.models import db, Users, Semantic_roles, Participants, Participant_relations,\
    Event_structure, Templates, Template_relations, Lexemes, Lexeme_relations, Forms, Parts_of_speech, Languages,\
    Examples, Event_structure_relations, Meanings, Labels
from itsdangerous import URLSafeSerializer
from re import sub, compile
from sqlalchemy import not_


@app.route('/edit/lexeme/<int:lex_id>', methods=['POST', 'GET'])
def edit_lexeme(lex_id):
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id not in [2, 3]:
        return Check.status()
    if request.method == 'GET':
        return render_template("edit_lexeme.html",
                               lex_id=lex_id,
                               Forms=Forms,
                               Languages=Languages,
                               Parts_of_speech=Parts_of_speech,
                               Lexemes=Lexemes,
                               Amend=Amend,
                               Check=Check,
                               Meanings=Meanings,
                               Examples=Examples,
                               Participant_relations=Participant_relations,
                               Participants=Participants
                               )

    elif request.method == 'POST':
        no_spaces_at_edges = compile(r'( +$|^ +)')
        request_lang = no_spaces_at_edges.sub('', request.form.get('language'))
        if Languages.query.filter_by(lang=request_lang).first():
            lang_id = Languages.query.filter_by(lang=request_lang).first().lang_id
        else:
            new_language = Languages(
                lang=request_lang
            )
            db.session.add(new_language)
            db.session.commit()
            lang_id = new_language.lang_id

        Lexemes.query.filter_by(lex_id=lex_id).update(
            {
                'lang_id': lang_id,
                'pos_id': request.form.get('pos')
            }
        )
        db.session.commit()

        forms_to_delete = [request.form.get(i) for i in request.form if
                         i.startswith('delete_form_') and request.form.get(i)]
        for form in forms_to_delete:
            Forms.query.filter_by(form_id=form).delete()
            Forms.query.filter_by(parent_id=form).delete()
            db.session.commit()

        all_forms = [i for i in request.form if
                     i.startswith('main_form_') and request.form.get(i)]
        for f in all_forms:
            if no_spaces_at_edges.sub('', request.form.get(f)):
                added_form = Forms(
                    form=no_spaces_at_edges.sub('', request.form.get(f)),
                    lex_id=lex_id,
                    type=1
                )
                db.session.add(added_form)
                db.session.commit()
            if no_spaces_at_edges.sub('', request.form.get(f'script_form_{f.split("_")[-1]}')):
                db.session.add(
                    Forms(
                        form=no_spaces_at_edges.sub('', request.form.get(f'script_form_{f.split("_")[-1]}')),
                        lex_id=lex_id,
                        type=2,
                        parent_id=added_form.form_id
                    )
                )
                db.session.commit()

        for f in [form for form in request.form if form.startswith(f'existent_form_')]:
            Forms.query.filter_by(form_id=int(f.split('_')[-1])).update(
                {'form': request.form.get(int(f.split('_')[-1]))}
            )
            Forms.query.filter_by(parent_id=int(form.split('_')[-1]), type=2).update(
                {'form': request.form.get(int(f.split('_')[-1]))}
            )
            db.session.commit()
        return Amend.flash('Изменения сохранены.', 'success', url_for('edit_lexeme', lex_id=lex_id))

@app.route('/edit/new_lexeme', methods=['POST', 'GET'])
def new_lexeme():
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id not in [2, 3]:
        return Check.status()

    if request.method == 'GET':
        return render_template("new_lexeme.html",
                               Taxonomy=Taxonomy,
                               Templates=Templates,
                               Topology=Topology,
                               Semantic_roles=Semantic_roles,
                               Participants=Participants,
                               Event_structure=Event_structure,
                               Parts_of_speech=Parts_of_speech,
                               Languages=Languages
                               )

    elif request.method == 'POST':
        no_spaces_at_edges = compile(r'( +$|^ +)')
        request_lang = no_spaces_at_edges.sub('', request.form.get('language'))
        if Languages.query.filter_by(lang=request_lang).first():
            lang_id = Languages.query.filter_by(lang=request_lang).first().lang_id
        else:
            new_language = Languages(
                lang=request_lang
            )
            db.session.add(new_language)
            db.session.commit()
            lang_id = new_language.lang_id

        lexeme = Lexemes(
            lang_id=lang_id,
            pos_id=request.form.get('pos')
        )
        db.session.add(lexeme)
        db.session.commit()

        all_forms = [i for i in request.form if
                     i.startswith('main_form_') and request.form.get(i)]
        for f in all_forms:
            if no_spaces_at_edges.sub('', request.form.get(f)):
                db.session.add(
                    Forms(
                        form=no_spaces_at_edges.sub('', request.form.get(f)),
                        lex_id=lexeme.lex_id,
                        type=1
                    )
                )
                db.session.commit()
            if no_spaces_at_edges.sub('', request.form.get(f'script_form_{f.split("_")[-1]}')):
                db.session.add(
                    Forms(
                        form=no_spaces_at_edges.sub('', request.form.get(f'script_form_{f.split("_")[-1]}')),
                        lex_id=lexeme.lex_id,
                        type=2
                    )
                )
                db.session.commit()
        return Amend.flash('Лексема добавлена.', 'success', url_for('edit_lexeme', lex_id=lexeme.lex_id))

@app.route('/lexemes', methods=['POST', 'GET'])
@app.route('/lexemes/<int:page>', methods=['POST', 'GET'])
def lexemes(page=1):
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id not in [2, 3]:
        return Check.status()

    if request.method == 'GET':
        page_of_lexemes = Lexemes.query.order_by(Lexemes.lex_id.desc()).paginate(page, 20)
        lexemes = page_of_lexemes.items
        return render_template("lexemes.html",
                               lexemes=lexemes,
                               items=page_of_lexemes,
                               Amend=Amend,
                               Forms=Forms,
                               Languages=Languages,
                               Parts_of_speech=Parts_of_speech,
                               Lexemes=Lexemes
                               )
    elif request.method == 'POST':
        if request.form.get('query'):
            if (request.form.get('parameter') == 'ID'):
                try:
                    lexemes = Lexemes.query.filter_by(lex_id=int(request.form.get('query'))).order_by(Lexemes.lex_id.desc()).all()
                    page_of_lexemes = None
                except:
                    return Amend.flash('Введите число.', 'danger', url_for('lexemes'))
            return render_template("lexemes.html",
                                   lexemes=lexemes,
                                   items=page_of_lexemes,
                                   Amend=Amend,
                                   Forms=Forms,
                                   Languages=Languages,
                                   Parts_of_speech=Parts_of_speech,
                                   Lexemes=Lexemes
                                   )
        return Amend.flash('Введите поисковый запрос.', 'danger', url_for('templates'))

@app.route('/edit/lexeme/<int:lex_id>/new_meaning', methods=['POST', 'GET'])
def new_meaning(lex_id):
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id not in [2, 3]:
        return Check.status()

    if request.method == 'GET':
        return render_template("new_meaning.html",
                               Labels=Labels,
                               Templates=Templates,
                               Semantic_roles=Semantic_roles,
                               Participants=Participants,
                               Event_structure=Event_structure,
                               Parts_of_speech=Parts_of_speech,
                               Languages=Languages,
                               Forms=Forms,
                               lex_id=lex_id,
                               not_=not_,
                               Participant_relations=Participant_relations
                               )

    elif request.method == 'POST':
        no_spaces_at_edges = compile(r'( +$|^ +)')
        example = Examples(
            example=no_spaces_at_edges.sub('', request.form.get('example', '')),
            original_script=no_spaces_at_edges.sub('', request.form.get('original_script', '')),
            translation=no_spaces_at_edges.sub('', request.form.get('translation', '')),
            source=no_spaces_at_edges.sub('', request.form.get('source', '')),
        )
        db.session.add(example)
        db.session.commit()
        meaning = Meanings(
            lex_id=lex_id,
            example_id=example.example_id,
            government=no_spaces_at_edges.sub('', request.form.get('government'))
        )
        db.session.add(meaning)
        db.session.commit()
        if request.form.get('based_on'):
            db.session.add(
                Template_relations(
                    templ_id=int(request.form.get('based_on')),
                    target_id=meaning.m_id,
                    type=4
                )
            )
            db.session.commit()

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
                Participant_relations(
                    participant_id=participant.participant_id,
                    target_id=meaning.m_id,
                    type=4
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

        event_structure = [(1, 'I'), (2, 'B'),
                           (3, 'P'), (4, 'F'),
                           (5, 'R'), (6, 'Impl')]
        for event_structure_part in event_structure:
            for i in [part for part in request.form if
                      part.startswith(f'{event_structure_part[-1]}_') and request.form.get(part)]:
                item = Event_structure(ese=no_spaces_at_edges.sub('', request.form.get(i)),
                                       rank=request.form.get(f'rank_{event_structure_part[-1]}_{i.split("_")[-1]}'),
                                       type=event_structure_part[0], status=request.form.get(f'status_ese_{event_structure_part[-1]}_{i.split("_")[-1]}')
                                       )
                db.session.add(item)
                db.session.commit()
                if request.form.get(f'is_child_{event_structure_part[-1]}_{i.split("_")[-1]}'):
                    db.session.add(
                        Event_structure_relations(
                            ese_id=item.ese_id,
                            target_id=request.form.get(f'is_child_{event_structure_part[-1]}_{i.split("_")[-1]}'),
                            type=1
                        )
                    )
                else:
                    db.session.add(
                        Event_structure_relations(
                            ese_id=item.ese_id,
                            target_id=int(request.form.get('based_on')),
                            type=1
                        )
                    )
                db.session.add(
                    Event_structure_relations(
                        ese_id=item.ese_id,
                        target_id=meaning.m_id,
                        type=2
                    )
                )
                db.session.commit()
        return Amend.flash('Значение добавлено.', 'success', url_for('edit_lexeme', lex_id=lex_id))

@app.route('/edit/meaning/<int:m_id>', methods=['POST', 'GET'])
def edit_meaning(m_id):
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id not in [2, 3]:
        return Check.status()
    if request.method == 'GET':
        return render_template("edit_meaning.html",
                               m=Meanings.query.get(m_id),
                               Labels=Labels,
                               Templates=Templates,
                               Template_relations=Template_relations,
                               Semantic_roles=Semantic_roles,
                               Participants=Participants,
                               Participant_relations=Participant_relations,
                               Examples=Examples,
                               Event_structure=Event_structure,
                               Event_structure_relations=Event_structure_relations,
                               Amend=Amend,
                               Check=Check,
                               not_=not_,
                               Forms=Forms
                               )

    elif request.method == 'POST':
        no_spaces_at_edges = compile(r'( +$|^ +)')
        m = Meanings.query.get(m_id)
        if request.form.get('based_on'):
            based_on = int(request.form.get('based_on'))
        else:
            based_on = None
        Examples.query.filter_by(example_id=m.example_id).update(
            {'example': no_spaces_at_edges.sub('', request.form.get('example', '')),
             'original_script': no_spaces_at_edges.sub('', request.form.get('original_script', '')),
             'translation': no_spaces_at_edges.sub('', request.form.get('translation', '')),
             'source': no_spaces_at_edges.sub('', request.form.get('source', ''))}
        )
        Meanings.query.filter_by(m_id=m_id).update(
            {'government': no_spaces_at_edges.sub('', request.form.get('government'))}
        )
        Template_relations.query.filter_by(target_id=m.m_id, type=4).update(
            {'templ_id': based_on}
        )
        db.session.commit()

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

        participants_to_delete = [request.form.get(i) for i in request.form if
                                  i.startswith('delete_p_') and request.form.get(i)]
        for p in participants_to_delete:
            Participants.query.filter_by(participant_id=p).delete()
            Participant_relations.query.filter_by(participant_id=p).delete()

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
                Participant_relations(
                    participant_id=participant.participant_id,
                    target_id=m_id,
                    type=4
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

        ese_to_delete = [request.form.get(i) for i in request.form if
                         i.startswith('delete_ese_') and request.form.get(i)]
        for ese in ese_to_delete:
            Event_structure_relations.query.filter_by(ese_id=ese).delete()
            Event_structure.query.filter_by(ese_id=ese).delete()
            db.session.commit()

        event_structure = [(1, 'I'), (2, 'B'),
                           (3, 'P'), (4, 'F'),
                           (5, 'R'), (6, 'Impl')]
        for event_structure_part in event_structure:
            for i in [part for part in request.form if
                      part.startswith(f'{event_structure_part[-1]}_') and request.form.get(part)]:
                item = Event_structure(ese=no_spaces_at_edges.sub('', request.form.get(i)),
                                       rank=request.form.get(f'rank_{event_structure_part[-1]}_{i.split("_")[-1]}'),
                                       type=event_structure_part[0], status=request.form.get(
                        f'status_ese_{event_structure_part[-1]}_{i.split("_")[-1]}')
                                       )
                db.session.add(item)
                db.session.commit()
                if request.form.get(f'is_child_{event_structure_part[-1]}_{i.split("_")[-1]}'):
                    db.session.add(
                        Event_structure_relations(
                            ese_id=item.ese_id,
                            target_id=request.form.get(f'is_child_{event_structure_part[-1]}_{i.split("_")[-1]}'),
                            type=1
                        )
                    )
                else:
                    db.session.add(
                        Event_structure_relations(
                            ese_id=item.ese_id,
                            target_id=based_on,
                            type=1
                        )
                    )
                db.session.add(
                    Event_structure_relations(
                        ese_id=item.ese_id,
                        target_id=m_id,
                        type=2
                    )
                )
                db.session.commit()
            for i in [part for part in request.form if
                      part.startswith(f'existent_{event_structure_part[-1]}_')]:
                i_id = int(i.split('_')[-1])
                Event_structure.query.filter_by(ese_id=i_id, type=event_structure_part[0]).update(
                    {'ese': no_spaces_at_edges.sub('', request.form.get(i)),
                     'rank': request.form.get(f'rank_existent_{event_structure_part[-1]}_{i.split("_")[-1]}'),
                     'status': request.form.get(f'status_ese_existent_{event_structure_part[-1]}_{i.split("_")[-1]}')}
                )
                db.session.commit()
                Event_structure_relations.query.filter_by(ese_id=i_id, type=1).delete()
                if request.form.get(f'is_child_existent_{event_structure_part[-1]}_{i.split("_")[-1]}'):
                    db.session.add(
                        Event_structure_relations(
                            ese_id=i_id,
                            target_id=request.form.get(f'is_child_existent_{event_structure_part[-1]}_{i.split("_")[-1]}'),
                            type=1
                        )
                    )
                else:
                    db.session.add(
                        Event_structure_relations(
                            ese_id=i_id,
                            target_id=int(request.form.get('based_on')),
                            type=1
                        )
                    )
                db.session.commit()
        db.session.commit()
        return Amend.flash('Изменения сохранены.', 'success', url_for('edit_meaning', m_id=m_id))