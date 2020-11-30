import copy

import guitarpro


def duplicateMeasureHeaders(song):
    newMeasureHeaders = []
    for mHeader in song.measureHeaders:
        previousStart = newMeasureHeaders[-1].start if len(newMeasureHeaders) > 0 else mHeader.start
        previousLength = newMeasureHeaders[-1].length if len(newMeasureHeaders) > 0 else 0

        hasDoubleBar = mHeader.hasDoubleBar
        mHeader.hasDoubleBar = False

        mHeader.number = mHeader.number * 2 - 1
        mHeader.start = previousStart + previousLength
        newMeasureHeaders.append(mHeader)

        newMheader = guitarpro.MeasureHeader(
            mHeader.number + 1,
            mHeader.start + mHeader.length,
            hasDoubleBar,
            mHeader.keySignature,
            mHeader.timeSignature,
            guitarpro.Tempo(mHeader.tempo.value),
            None,
            mHeader.isRepeatOpen,
            mHeader.repeatAlternative,
            mHeader.repeatClose,
            mHeader.tripletFeel,
            mHeader.direction,
            mHeader.fromDirection
        )
        newMeasureHeaders.append(newMheader)

    song.measureHeaders = newMeasureHeaders


def duplicateTrackMeasures(song):
    for track in song.tracks:
        newMeasures = []
        for measure in track.measures:
            newMeasureLength = int(measure.length / 2)
            beatsForVoicesFirstMeasure = []
            beatsForVoicesSecondMeasure = []
            for voice in measure.voices:
                beatsFirstMeasure = []
                beatsSecondMeasure = []

                for beat in voice.beats:
                    if beat.status == guitarpro.BeatStatus.empty:
                        beatsFirstMeasure.append(beat)
                        beatsSecondMeasure.append(beat)
                    else:
                        time = sum([x.duration.time for x in beatsFirstMeasure])
                        if time < newMeasureLength:
                            if time + beat.duration.time <= newMeasureLength:
                                beatsFirstMeasure.append(beat)
                            else:
                                timeLeftInFirstMeasure = newMeasureLength - time
                                firstDuration = timeLeftInFirstMeasure
                                secondDuration = beat.duration.time - firstDuration
                                durationTimes = [
                                    firstDuration,
                                    secondDuration
                                ]

                                success = False
                                while not success:
                                    try:
                                        durations = []
                                        for durationTime in durationTimes:
                                            durations.append(guitarpro.Duration.fromTime(durationTime))
                                        success = True
                                    except ValueError:
                                        None

                                    if not success:
                                        # Split longest beat
                                        smallestDuration = min(durationTimes)
                                        longestIndex = durationTimes.index(max(durationTimes))
                                        durationTimes[longestIndex] = durationTimes[longestIndex] - smallestDuration
                                        durationTimes.insert(longestIndex, smallestDuration)

                                beat.duration = guitarpro.Duration.fromTime(durationTimes[0])
                                beatsFirstMeasure.append(beat)
                                timeLeftInFirstMeasure -= beat.duration.time

                                for durationTime in durationTimes[1:]:
                                    newBeat = guitarpro.Beat(
                                        voice,
                                        [],  # Notes are added below
                                        guitarpro.Duration.fromTime(durationTime),
                                        None,
                                        beat.start,  # TODO calculate
                                        beat.effect,
                                        beat.index,
                                        beat.octave,
                                        beat.display,
                                        beat.status
                                    )

                                    newNotes = []
                                    for note in beat.notes:
                                        newNotes.append(guitarpro.Note(
                                            newBeat,
                                            note.value,
                                            note.velocity,
                                            note.string,
                                            note.effect,
                                            note.durationPercent,
                                            note.swapAccidentals,
                                            guitarpro.NoteType.tie
                                        ))

                                    newBeat.notes = newNotes

                                    if (timeLeftInFirstMeasure > 0):
                                        beatsFirstMeasure.append(newBeat)
                                        timeLeftInFirstMeasure - newBeat.duration.time
                                    else:
                                        beatsSecondMeasure.append(newBeat)

                        else:
                            beatsSecondMeasure.append(beat)

                beatsForVoicesFirstMeasure.append(beatsFirstMeasure)
                beatsForVoicesSecondMeasure.append(beatsSecondMeasure)

            newVoices = []

            for i in range(len(measure.voices)):
                measure.voices[i].beats = beatsForVoicesFirstMeasure[i]
                newVoices.append(guitarpro.Voice(
                    measure,
                    beatsForVoicesSecondMeasure[i],
                    measure.voices[i].direction
                ))

            newMeasures.append(measure)

            copy = guitarpro.Measure(
                measure.track,
                song.measureHeaders[measure.number],
                measure.clef,
                newVoices,
                measure.lineBreak
            )
            newMeasures.append(copy)

        track.measures = newMeasures


def doubleTempo(song):
    song.tempo *= 2

    for measureHeader in song.measureHeaders:
        measureHeader.tempo.value *= 2

    for track in song.tracks:
        for measure in track.measures:
            for voice in measure.voices:
                for beat in voice.beats:
                    if beat.effect.mixTableChange is not None:
                        if beat.effect.mixTableChange.tempo is not None:
                            mtc = beat.effect.mixTableChange
                            tempoItem = beat.effect.mixTableChange.tempo
                            beat.effect = guitarpro.BeatEffect(
                                beat.effect.stroke,
                                beat.effect.hasRasgueado,
                                beat.effect.pickStroke,
                                beat.effect.chord,
                                beat.effect.fadeIn,
                                beat.effect.tremoloBar,
                                guitarpro.MixTableChange(
                                    mtc.instrument,
                                    mtc.volume,
                                    mtc.balance,
                                    mtc.chorus,
                                    mtc.reverb,
                                    mtc.phaser,
                                    mtc.tremolo,
                                    mtc.tempoName,
                                    guitarpro.MixTableItem(
                                        tempoItem.value * 2,
                                        tempoItem.duration,
                                        tempoItem.allTracks
                                    ),
                                    mtc.hideTempo,
                                    mtc.wah,
                                    mtc.useRSE,
                                    mtc.rse
                                ),
                                beat.effect.slapEffect,
                                beat.effect.vibrato
                            )


def doubleNoteValues(song):
    for track in song.tracks:
        for measure in track.measures:
            for voice in measure.voices:
                for beat in voice.beats:
                    beat.duration = guitarpro.Duration.fromTime(beat.duration.time * 2)


def convertIntroToTriplets(song):
    startMeasureIndex = 0
    endMeasureIndex = 31

    song.tempo = int(song.tempo * 2 / 3)

    for track in song.tracks:
        for measureToRemoveFrom in track.measures[startMeasureIndex:endMeasureIndex + 1]:
            for voice in measureToRemoveFrom.voices:
                for beat in voice.beats:
                    if beat.status is not guitarpro.BeatStatus.empty:
                        beat.duration = guitarpro.Duration.fromTime(int(beat.duration.time * 2 / 3))

    # Tranform from 3/4 to 4/4
    for measureHeader in song.measureHeaders[startMeasureIndex:endMeasureIndex + 1]:
        measureHeader.timeSignature = guitarpro.TimeSignature(
            int(measureHeader.timeSignature.numerator * 2 / 3),
            measureHeader.timeSignature.denominator,
            measureHeader.timeSignature.beams
        )

    # Combine 2/4 measures
    for measureHeader in song.measureHeaders[startMeasureIndex:endMeasureIndex + 1]:
        measureHeader.timeSignature = guitarpro.TimeSignature(
            int(measureHeader.timeSignature.numerator * 2),
            measureHeader.timeSignature.denominator,
            measureHeader.timeSignature.beams
        )

    measuresToRemoveNotesFrom = list(range(startMeasureIndex + 1, endMeasureIndex + 1, 2))
    measuresToRemoveNotesFrom.reverse()

    for i in measuresToRemoveNotesFrom:
        del song.measureHeaders[i]

    for track in song.tracks:
        for i in measuresToRemoveNotesFrom:
            measureToRemoveFrom = track.measures[i]
            measureToMoveInto = track.measures[i - 1]
            for voice in measureToRemoveFrom.voices:
                for beat in voice.beats:
                    if beat.status is not guitarpro.BeatStatus.empty:
                        measureToMoveInto.voices[measureToRemoveFrom.voices.index(voice)].beats.append(beat)

            del track.measures[i]


def cleanMeasures(song):
    for track in song.tracks:
        for measure in track.measures:
            for voice in measure.voices:
                isVoiceEmpty = True

                for beat in voice.beats:
                    if beat.status == guitarpro.BeatStatus.normal:
                        isVoiceEmpty = False

                if isVoiceEmpty:
                    voice.beats = []


def fixVolume(song):
    for track in song.tracks:
        if track.channel.volume == 48:
            track.channel.volume += 70


song = guitarpro.parse('/Users/eela/Documents/Guitar Pro/Muut/Metallica - Disposable Heroes GP5.gp5')

duplicateMeasureHeaders(song)
duplicateTrackMeasures(song)
doubleTempo(song)
doubleNoteValues(song)

# convertIntroToTriplets(song)

cleanMeasures(song)

# fixVolume(song)

# TODO Fix volume automations

guitarpro.write(song, '/Users/eela/Documents/Guitar Pro/Muut/Metallica - Disposable Heroes korjattu.gp5')
