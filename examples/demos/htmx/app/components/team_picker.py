from app.citry_app import citry_app
from app.data import Team
from citry import Component


class TeamPicker(Component):
    citry = citry_app

    class Kwargs:
        department: str
        teams: tuple[Team, ...]

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots):
        count = len(kwargs.teams)
        return {
            "teams": kwargs.teams,
            "has_teams": bool(kwargs.teams),
            "summary": f"{count} team{'s' if count != 1 else ''} available",
        }

    template = """
      <div class="team-picker-fragment">
        <label for="team-choice">Team</label>
        <select id="team-choice" name="team" c-disabled="not has_teams">
          <c-if cond="has_teams">
            <c-for each="team in teams">
              <option c-value="team.id">{{ team.name }}</option>
            </c-for>
          </c-if>
          <c-else>
            <option value="">No teams available</option>
          </c-else>
        </select>
        <small role="status">{{ summary }}</small>
      </div>
    """

    css = """
      .team-picker-fragment {
        display: grid;
        gap: 0.3rem;
      }
      .team-picker-fragment label {
        color: var(--color-text);
        font-size: 0.82rem;
        font-weight: 650;
      }
      .team-picker-fragment select {
        min-height: 2.55rem;
        padding: 0.45rem 0.65rem;
        border: 1px solid var(--color-input-border);
        border-radius: 0.375rem;
        color: var(--color-text);
        background: var(--color-input);
      }
      .team-picker-fragment small {
        color: var(--color-muted);
      }
    """
